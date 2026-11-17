---
date: 2026-12-02
slug: openshift-routes-tls
authors:
  - bhry98
categories:
  - OpenShift
  - Security
description: How OpenShift Routes work, the three TLS termination types (edge, passthrough, re-encrypt), when to use each, and how to debug the "Application is not available" page.
---

# OpenShift Routes: Edge, Passthrough and Re-encrypt TLS Explained

A Route is how traffic from outside the cluster reaches your app on OpenShift. Creating one takes a
single command; choosing **where TLS ends** is the decision that actually matters, for security,
for features and for debugging. This post explains the three options and when I use each.

<!-- more -->

## How a request reaches your pod

```text
Client ──► DNS *.apps.cluster.example.com
       ──► Router (HAProxy pods, the default IngressController)
       ──► Service  (selects pods by label)
       ──► Pod      (ready endpoints only)
```

The **router** runs HAProxy and watches every Route in the cluster. A wildcard DNS record points
`*.apps.<cluster-domain>` at it, so any Route under that domain works without touching DNS. For a
custom domain, point a CNAME at the router.

## Plain HTTP

```bash
oc expose service orders-api
oc get route orders-api
# orders-api-orders-dev.apps.cluster.example.com
```

Fine for a quick test. For anything real, pick one of the TLS types below.

## 1. Edge: TLS ends at the router

```text
Client ══TLS══► Router ──HTTP──► Pod
```

```bash
oc create route edge orders-api \
  --service=orders-api \
  --hostname=orders.example.com \
  --cert=tls.crt --key=tls.key --ca-cert=ca.crt \
  --insecure-policy=Redirect
```

- Without `--cert`, the router uses the cluster's default wildcard certificate.
- `--insecure-policy=Redirect` sends `http://` traffic to `https://`.
- The router can read HTTP, so you get **path-based routing**, **sticky sessions** (cookies) and
  **`X-Forwarded-For` / `X-Forwarded-Proto`** headers.

**Use it for:** most web apps and APIs, when traffic inside the cluster network is acceptable in
plain HTTP.

!!! warning "Spring Boot behind an edge route"
    Your app sees HTTP, so generated redirects and links may use `http://`. Set
    `server.forward-headers-strategy=framework` (or `native`) so Spring trusts
    `X-Forwarded-Proto`.

## 2. Passthrough: TLS goes all the way to the pod

```text
Client ══════════TLS══════════► Pod   (router only reads the SNI hostname)
```

```bash
oc create route passthrough orders-api \
  --service=orders-api \
  --hostname=orders.example.com
```

- The router never decrypts. It picks the backend using **SNI** from the TLS handshake.
- The **pod holds the certificate** and serves TLS itself.
- No path routing, no cookies, no forwarded headers: the router cannot see HTTP.

**Use it for:** **mutual TLS** where the app must see the client certificate (bank or partner
integrations, for example IBM ACE or API gateways doing mTLS), non-HTTP protocols over TLS, and
compliance rules that forbid decrypting at the edge.

## 3. Re-encrypt: TLS at the router, and again to the pod

```text
Client ══TLS══► Router ══TLS══► Pod
```

```bash
oc create route reencrypt orders-api \
  --service=orders-api \
  --hostname=orders.example.com \
  --cert=tls.crt --key=tls.key
```

You get edge features (path routing, headers, cookies) **and** encryption inside the cluster. The
router must trust the pod's certificate. The easy way is a **service serving certificate**, signed
automatically by OpenShift's service CA:

```bash
oc annotate service orders-api \
  service.beta.openshift.io/serving-cert-secret-name=orders-api-tls
```

OpenShift creates the secret `orders-api-tls` (`tls.crt`, `tls.key`) and rotates it. Mount it in
the pod and serve HTTPS on 8443. For a re-encrypt route with no `destinationCACertificate`, the
router trusts the service CA automatically.

```yaml
# Spring Boot: serve HTTPS with the mounted PEM files
server:
  port: 8443
  ssl:
    certificate: /etc/tls/tls.crt
    certificate-private-key: /etc/tls/tls.key
```

**Use it for:** regulated environments that require encryption in transit everywhere, while still
needing router features.

## Side by side

| | Edge | Passthrough | Re-encrypt |
|---|---|---|---|
| Where TLS ends | Router | Pod | Router, then new TLS to pod |
| Encrypted inside cluster | No | Yes | Yes |
| Certificate on | Router | Pod | Both |
| Path-based routing | Yes | No | Yes |
| Sticky sessions (cookie) | Yes | No | Yes |
| `X-Forwarded-*` headers | Yes | No | Yes |
| Client certificate (mTLS) seen by app | No | **Yes** | No |
| Complexity | Low | Medium | Medium |

## Useful annotations

```bash
# Long-running requests (default is 30s)
oc annotate route orders-api haproxy.router.openshift.io/timeout=120s

# Load-balancing algorithm
oc annotate route orders-api haproxy.router.openshift.io/balance=roundrobin
```

## Route or Ingress?

Both work. If you create a Kubernetes `Ingress`, OpenShift generates a Route from it, and you can
choose the termination with an annotation such as `route.openshift.io/termination: reencrypt`.
I use **Ingress** when the same manifests must run on other Kubernetes clusters, and **Route** when
I need passthrough, re-encrypt or router annotations without workarounds.

## "Application is not available"

That page is the router saying: *I have a Route, but no ready pod behind it.* Check in this order:

```bash
oc get endpoints orders-api             # empty? nothing is ready or selected
oc get pods -l app=orders-api           # are pods Running and READY 1/1?
oc describe svc orders-api              # selector and targetPort match the pod?
oc get route orders-api -o yaml         # spec.to.name and spec.port.targetPort correct?
```

The usual causes: a failing **readiness probe**, a **selector** that does not match the pod
labels, or a **targetPort** that points at the wrong port name. For passthrough and re-encrypt, also
check that the pod actually serves TLS on that port.

## Takeaway

- **Edge** for most apps: simple, full HTTP features.
- **Passthrough** when the app must own TLS, especially for mTLS.
- **Re-encrypt** when you need router features *and* encryption everywhere; service serving
  certificates make it nearly free.

Previous: [Why your container fails on OpenShift](openshift-scc-arbitrary-uid.md) ·
Next: [Debugging pods on OpenShift: my oc playbook](openshift-debugging-pods.md)
