---
date: 2026-12-16
slug: spring-boot-openshift-builds
authors:
  - bhry98
categories:
  - Spring Boot
  - OpenShift
description: Four ways to turn a Spring Boot app into an image for OpenShift (Dockerfile in CI, in-cluster Docker builds, Source-to-Image, Jib) with commands, trade-offs and how I choose.
---

# Building Spring Boot Images for OpenShift: Dockerfile, S2I or Jib?

There are at least four reasonable ways to get a Spring Boot JAR running as an image on OpenShift.
They all work. They differ in **where the build runs**, **who controls the base image** and **how
much CI you need**. Here is each one with real commands, and how I pick between them.

<!-- more -->

## Option 1: Dockerfile, built in CI, pushed to a registry

The most portable approach. GitLab CI (or Jenkins, GitHub Actions) builds the image and pushes it
to Nexus, Quay or Harbor; OpenShift only pulls and runs it.

```dockerfile
FROM registry.access.redhat.com/ubi9/openjdk-21 AS build
USER 0
WORKDIR /src
COPY . .
RUN ./mvnw -q -DskipTests package

FROM registry.access.redhat.com/ubi9/openjdk-21-runtime
COPY --from=build /src/target/*.jar /deployments/app.jar
EXPOSE 8080
```

```yaml
# .gitlab-ci.yml (simplified)
build-image:
  image: quay.io/buildah/stable
  script:
    - buildah bud -t $REGISTRY/orders-api:$CI_COMMIT_SHORT_SHA .
    - buildah push $REGISTRY/orders-api:$CI_COMMIT_SHORT_SHA

deploy:
  image: registry.redhat.io/openshift4/ose-cli
  script:
    - oc login --token=$OC_TOKEN --server=$OC_SERVER
    - oc set image deployment/orders-api orders-api=$REGISTRY/orders-api:$CI_COMMIT_SHORT_SHA
    - oc rollout status deployment/orders-api
```

The UBI OpenJDK runtime image runs `/deployments/*.jar` automatically, works with OpenShift's
random UID, and sizes the heap from the container limit.

**Good:** same image everywhere, full control, no build load on the cluster.
**Cost:** you maintain the CI pipeline and the registry.

## Option 2: Docker strategy, built inside OpenShift

Same Dockerfile, but OpenShift builds it with a **BuildConfig** and stores the result in the
internal registry.

```bash
oc new-build --strategy=docker --binary --name=orders-api
oc start-build orders-api --from-dir=. --follow
oc new-app orders-api                  # first deploy
oc expose service orders-api
```

**Good:** no registry or Docker daemon needed outside the cluster. Handy for small teams and
disconnected environments.
**Cost:** builds use cluster CPU and memory; the cluster admin may restrict the Docker strategy.

## Option 3: Source-to-Image (S2I)

No Dockerfile at all. You give OpenShift **source code** (or a JAR), and a **builder image** knows
how to build and run Java.

From Git:

```bash
oc new-app registry.access.redhat.com/ubi9/openjdk-21~https://gitlab.example.com/team/orders-api.git \
  --name=orders-api
```

Or from a JAR you already built:

```bash
oc new-build registry.access.redhat.com/ubi9/openjdk-21 --binary --name=orders-api
./mvnw -q -DskipTests package
oc start-build orders-api --from-file=target/orders-api.jar --follow
```

**Good:** developers only push code; Red Hat maintains the base image, so rebuilding picks up
security patches.
**Cost:** less control over the image layout; OpenShift-specific.

## Option 4: Jib, no Dockerfile and no Docker daemon

Jib, a Maven/Gradle plugin from Google, builds layered images directly from the build tool.
Dependencies, resources and classes go in separate layers, so a code change pushes only a few KB.

```xml
<plugin>
  <groupId>com.google.cloud.tools</groupId>
  <artifactId>jib-maven-plugin</artifactId>
  <version>3.4.4</version>
  <configuration>
    <from><image>registry.access.redhat.com/ubi9/openjdk-21-runtime</image></from>
    <to><image>nexus.example.com:8443/team/orders-api</image></to>
    <container>
      <user>185</user>
      <ports><port>8080</port></ports>
    </container>
  </configuration>
</plugin>
```

```bash
./mvnw compile jib:build -Djib.to.tags=$CI_COMMIT_SHORT_SHA
```

**Good:** fast incremental builds, reproducible, runs in any CI container without privileges.
**Cost:** Java-only; you still need a registry.

!!! note "Cloud Native Buildpacks"
    `./mvnw spring-boot:build-image` (Paketo Buildpacks) is a fifth option with good defaults. It
    needs a Docker-compatible daemon at build time, which is often the deciding factor in CI.

## Comparison

| | Dockerfile in CI | Docker strategy | S2I | Jib |
|---|---|---|---|---|
| Build runs in | CI | OpenShift | OpenShift | CI / laptop |
| Needs Dockerfile | Yes | Yes | No | No |
| Needs Docker daemon | No (Buildah/Kaniko) | No | No | No |
| External registry | Yes | No | No | Yes |
| Portable to other K8s | **Yes** | Image only | Image only | **Yes** |
| Incremental speed | Good (layer cache) | Good | Medium | **Best** |
| Base image patching | You | You | **Red Hat** | You |

## Triggering the deploy

Whatever builds the image, roll it out in one of two ways:

```bash
# Explicit: CI sets the new tag (clear audit trail, easy rollback)
oc set image deployment/orders-api orders-api=nexus.example.com:8443/team/orders-api:1.4.2
oc rollout status deployment/orders-api
oc rollout undo deployment/orders-api        # if needed

# Automatic: redeploy when an ImageStream tag changes (in-cluster builds)
oc set triggers deployment/orders-api --from-image=orders-api:latest -c orders-api
```

## How I choose

- **Team already has GitLab CI and a registry:** Dockerfile (or Jib) in CI, `oc set image` to
  deploy. Portable, auditable, and the cluster only runs workloads.
- **Small team, no external registry, or a disconnected cluster:** binary **S2I** with the UBI
  OpenJDK builder. Least to maintain.
- **Many Java microservices with frequent builds:** **Jib**, for layer reuse and speed.

Whichever you choose, the runtime rules stay the same: non-root image, port 8080, probes on
Actuator, graceful shutdown. They are all in [Running Spring Boot on OpenShift](spring-boot-on-openshift.md).

Previous: [Debugging pods on OpenShift](../openshift/openshift-debugging-pods.md)
