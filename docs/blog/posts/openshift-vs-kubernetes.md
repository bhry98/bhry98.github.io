---
date: 2026-11-18
slug: openshift-vs-kubernetes
authors:
  - bhry98
categories:
  - OpenShift
description: OpenShift is Kubernetes with opinions. What it adds on top (Routes, SCCs, built-in OAuth, image streams, builds, Operators) and when that is worth it.
---

# OpenShift Is Not Just Kubernetes: What You Actually Get

"OpenShift is just Kubernetes with a Red Hat logo." I hear this often, and it is half true. Every
OpenShift cluster *is* a conformant Kubernetes cluster: your Deployments, Services and ConfigMaps
work as they do anywhere else. The difference is everything Red Hat decided you should not have to
assemble yourself. This post walks through what those decisions are and when they are worth it.

<!-- more -->

## The short version

Plain Kubernetes gives you an engine. OpenShift gives you the car: engine, brakes, dashboard,
seatbelts already fastened. You lose some freedom to pick parts, and you gain a platform that a
small team can run in production.

| Concern | Plain Kubernetes | OpenShift |
|---|---|---|
| Exposing apps over HTTP(S) | Choose and install an Ingress controller | **Routes** + HAProxy router, installed |
| Pod security | Pod Security Admission, you set the policy | **SCCs**, restricted by default |
| Login & users | Bring your own (OIDC, certs…) | **Built-in OAuth server** (LDAP, OIDC, htpasswd) |
| Image registry | Install one | **Integrated registry** + ImageStreams |
| Building images | External CI | **BuildConfig** (S2I, Docker) in-cluster |
| Monitoring | Install Prometheus stack | **Prometheus + Alertmanager** preinstalled |
| Cluster upgrades | Distro-specific | **Cluster Version Operator**, one click / one command |
| Node OS | Any Linux | **RHCOS**, immutable and managed by the cluster |
| CLI | `kubectl` | `oc` (a superset of `kubectl`) |

## 1. Projects instead of bare namespaces

A **Project** is a namespace with extras: a display name, a description, and a template that can
attach default quotas, limit ranges and network policies the moment it is created. Developers can
be allowed to create their own projects (`oc new-project`) without being cluster admins.

```bash
oc new-project orders-dev --display-name="Orders (dev)"
oc get project orders-dev -o yaml
```

## 2. Routes: ingress that is already there

Every cluster ships with an **ingress controller** (HAProxy) and a wildcard DNS name like
`*.apps.cluster.example.com`. Exposing a service is one command:

```bash
oc expose service orders-api                          # plain HTTP
oc create route edge orders-api --service=orders-api  # HTTPS, TLS ends at the router
```

Routes also support **passthrough** and **re-encrypt** TLS, which I cover in
[OpenShift Routes explained](openshift-routes-tls.md). Standard `Ingress` objects still work:
OpenShift converts them to Routes for you.

## 3. Secure by default (and why your image breaks)

This is the one that surprises people most. OpenShift does **not** let containers run as root by
default. The `restricted-v2` **Security Context Constraint (SCC)** runs each pod with a random,
high user ID taken from a range assigned to the project, drops all Linux capabilities and blocks
privilege escalation.

Images from Docker Hub that assume root (write to `/var/cache/nginx`, bind to port 80) fail on day
one. That is a feature: it is the same hardening you should be doing anyway. The full story and the
fix are in [Why your container fails on OpenShift](openshift-scc-arbitrary-uid.md).

## 4. Authentication is built in

OpenShift runs its own **OAuth server**. Point it at LDAP / Active Directory, an OIDC provider such
as **Keycloak**, or GitHub, and users log in to the console and the CLI with their existing
accounts. Groups can be synced from LDAP and bound to roles.

```bash
oc login --web https://api.cluster.example.com:6443
oc whoami
oc adm groups new platform-admins
oc adm policy add-cluster-role-to-group cluster-admin platform-admins
```

## 5. Registry, ImageStreams and Builds

The cluster includes an **image registry**. On top of it, an **ImageStream** is a pointer to images
(internal or external) that can **trigger a redeploy** when a tag changes. **BuildConfigs** build
images inside the cluster from a Git repo or a binary upload, using Source-to-Image (S2I) or a
Dockerfile. You do not *have* to use them (many teams build in GitLab CI and push to Nexus or
Quay), but for small teams they remove a lot of plumbing. I compare the options for Java in
[Building Spring Boot images for OpenShift](spring-boot-openshift-builds.md).

## 6. Operators run the cluster, and your middleware

OpenShift is managed by **Operators**: the **Cluster Version Operator** upgrades the whole
platform, the **Machine Config Operator** manages node configuration, and so on. The same model is
offered to you through **OperatorHub**: install Kafka (AMQ Streams), databases, Keycloak (Red Hat
build of Keycloak), service mesh, GitOps (Argo CD) or IBM Cloud Pak for Integration with a few
clicks, and the operator handles day-2 tasks like upgrades and failover.

```bash
oc get clusterversion
oc get clusteroperators   # the health of every platform component
```

## 7. Observability out of the box

Prometheus, Alertmanager and dashboards for the platform are **preinstalled**. You can enable
**user workload monitoring** to scrape your own apps (for example Spring Boot's
`/actuator/prometheus`) with a `ServiceMonitor`, no extra Prometheus to run.

## When OpenShift is worth it

**Choose OpenShift when:**

- you run in a regulated environment (banking, government, healthcare) that needs vendor support,
  certifications and hardened defaults;
- the team is small and cannot afford to assemble and patch ten components by hand;
- you run vendor software certified on OpenShift (IBM Cloud Pak, for example);
- you need the same platform on-prem, in the cloud and at the edge.

**Plain Kubernetes (or a managed service) may be enough when:**

- you are cloud-native on a single provider and happy with EKS / AKS / GKE;
- you want full control over every component;
- budget is the main constraint (OpenShift is a subscription; **OKD** is the free upstream).

## Takeaway

OpenShift's value is not one big feature. It is dozens of decisions already made: secure defaults,
integrated login, routing, registry, monitoring and push-button upgrades. If those are decisions
your team would otherwise make (and maintain) itself, OpenShift saves real time. If not, plain
Kubernetes is a perfectly good engine.

Next in this series: [why your container fails on OpenShift, and how to fix it properly](openshift-scc-arbitrary-uid.md).
