---
date: 2026-11-25
slug: openshift-scc-arbitrary-uid
authors:
  - bhry98
categories:
  - OpenShift
  - Security
description: Why images that work everywhere fail on OpenShift with "Permission denied", how Security Context Constraints and the random UID work, and how to fix the image instead of weakening the cluster.
---

# Why Your Container Fails on OpenShift (and How to Fix It Properly)

The image runs fine with `docker run`. It runs fine on your Kubernetes cluster. You deploy it to
OpenShift and the pod goes straight into `CrashLoopBackOff` with `Permission denied`. The quick fix
most people find on the internet is `anyuid`. Here is why that is usually the wrong fix, and what
to do instead.

<!-- more -->

## The symptoms

```text
nginx: [emerg] mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)
```

```text
Error: listen EACCES: permission denied 0.0.0.0:80
```

```text
chown: changing ownership of '/data': Operation not permitted
```

Different apps, same cause: the image assumes it runs as **root** (or as one specific user), and on
OpenShift it does not.

## What OpenShift actually does

Every pod is admitted through a **Security Context Constraint (SCC)**. Ordinary workloads get
`restricted-v2`, which:

- runs the container as a **random UID** from a range reserved for the project;
- adds the user to the **root group (GID 0)**, but gives it no root privileges;
- **drops all Linux capabilities** and blocks privilege escalation;
- applies the default seccomp profile.

You can see the range assigned to your project:

```bash
oc get namespace orders-dev -o yaml | grep sa.scc
#   openshift.io/sa.scc.uid-range: 1000680000/10000
```

And check which SCC a running pod received and which user it runs as:

```bash
oc get pod orders-api-7d9c-xkq2 -o jsonpath='{.metadata.annotations.openshift\.io/scc}{"\n"}'
# restricted-v2
oc rsh orders-api-7d9c-xkq2 id
# uid=1000680000(1000680000) gid=0(root) groups=0(root),1000680000
```

So the process is user `1000680000`, which owns nothing in the image. Any directory owned by
`root:root` with mode `755` is read-only to it. Ports below 1024 need a capability it does not
have.

## Why not just grant `anyuid`?

```bash
oc adm policy add-scc-to-user anyuid -z default   # please don't
```

This lets every pod using the `default` service account in the project run as **any user,
including root**. A container escape now starts from root on the node. On a shared or regulated
cluster, it also tends to fail the next security review. And it hides the real problem: the image
is not built to run unprivileged, which is a good practice on *any* platform.

## The proper fix: build images that run as any user

The rule is simple. **Whatever the app needs to write must be owned by group 0 and
group-writable.** Because the random user is always a member of group 0, it gets access.

```dockerfile
FROM registry.access.redhat.com/ubi9/ubi-minimal

RUN microdnf install -y nginx && microdnf clean all

# 1. Writable paths: group 0 + same permissions as the owner
RUN mkdir -p /var/cache/nginx /var/log/nginx /run/nginx \
 && chgrp -R 0 /var/cache/nginx /var/log/nginx /run/nginx /etc/nginx \
 && chmod -R g=u /var/cache/nginx /var/log/nginx /run/nginx /etc/nginx

# 2. Listen on an unprivileged port. In nginx.conf also set:
#    listen 8080;  and  pid /run/nginx/nginx.pid;
EXPOSE 8080

# 3. A numeric, non-root user (OpenShift will override the UID anyway)
USER 1001

CMD ["nginx", "-g", "daemon off;"]
```

Three habits cover most cases:

1. **`chgrp -R 0 <dir> && chmod -R g=u <dir>`** for every path the app writes to.
2. **Listen on 8080 / 8443**, never 80 / 443. The Service and Route map the public port.
3. **Use a numeric `USER`**, never `root`, and do not `chown` at runtime.

!!! tip "Ready-made images"
    Many projects publish unprivileged variants: `nginxinc/nginx-unprivileged`, Bitnami images, and
    Red Hat **UBI** images (`ubi9/nginx-124`, `ubi9/openjdk-21-runtime`, `ubi9/postgresql-16`) are
    built for the random UID out of the box.

### Volumes

For persistent volumes, OpenShift sets an **fsGroup** from the project range, so the mounted volume
is writable by the pod. Do not run an init container that `chown`s the volume: it needs root and
will be rejected.

### Apps that need a username

A few tools (older Java libraries, SSH, some Python packages) call `getpwuid()` and crash when the
UID has no entry in `/etc/passwd`. UBI-based images handle this. In your own images you can make
`/etc/passwd` group-writable and add the entry in an entrypoint script:

```bash
#!/bin/sh
if ! whoami >/dev/null 2>&1; then
  echo "app:x:$(id -u):0:app user:/app:/sbin/nologin" >> /etc/passwd
fi
exec "$@"
```

## When you genuinely need another SCC

Some workloads need more: a vendor image you cannot rebuild, a monitoring agent that reads host
files. Then:

1. **Ask OpenShift** which SCC would admit the pod:

    ```bash
    oc policy scc-subject-review -f deployment.yaml
    ```

2. **Create a dedicated service account** and grant the SCC only to it, never to `default`:

    ```bash
    oc create serviceaccount legacy-app
    oc adm policy add-scc-to-user anyuid -z legacy-app
    oc set serviceaccount deployment/legacy-app legacy-app
    ```

3. **Document why**, and add it to the list of exceptions you review regularly.

`privileged` should stay reserved for platform components such as CSI drivers and node agents.

## Checklist

- [x] Writable paths owned by group 0 with `g=u` permissions
- [x] App listens on a port above 1024
- [x] Numeric non-root `USER` in the Dockerfile
- [x] No runtime `chown`, no root init containers
- [x] Extra SCCs only through a dedicated service account, with a reason

Images that follow these rules run on OpenShift, on vanilla Kubernetes with Pod Security
`restricted`, and on any hardened Docker host. Fixing the image once is cheaper than defending an
exception forever.

Previous: [OpenShift is not just Kubernetes](openshift-vs-kubernetes.md) ·
Next: [OpenShift Routes: edge, passthrough and re-encrypt TLS](openshift-routes-tls.md)
