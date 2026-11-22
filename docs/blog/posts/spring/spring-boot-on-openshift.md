---
date: 2026-10-28
slug: spring-boot-on-openshift
authors:
  - bhry98
categories:
  - Spring Boot
  - OpenShift
description: A production checklist for running Spring Boot services on Red Hat OpenShift. Images, health probes, configuration, memory and graceful shutdown.
---

# Running Spring Boot on OpenShift

Getting a Spring Boot service to *start* on OpenShift takes five minutes. Getting it to behave well
in production (rolling updates without errors, sensible memory use, configuration per environment)
takes a few deliberate choices. This is the checklist I follow.

<!-- more -->

## 1. Build an image that runs as any user

OpenShift runs containers with a **random, non-root user ID** that belongs to the root group. Images
that assume root, or write to directories only their owner can write to, fail at startup.

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY . .
RUN ./mvnw -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/*.jar app.jar
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
```

Two details matter here:

- **Port 8080.** Ports below 1024 need privileges the container won't have.
- **`-XX:MaxRAMPercentage=75`.** The JVM sizes its heap from the container's memory limit, leaving
  room for metaspace, threads and native memory. Without it you get either a wasted limit or an
  `OOMKilled` pod.

!!! tip
    Red Hat's UBI OpenJDK images (`ubi9/openjdk-21-runtime`) are built for this environment and are
    a good choice when you need a supported base image.

## 2. Use Actuator for health probes

Spring Boot Actuator exposes separate **liveness** and **readiness** groups. They are enabled
automatically when the app detects Kubernetes, and you can turn them on explicitly:

```yaml
# application.yaml
management:
  endpoint:
    health:
      probes:
        enabled: true
  endpoints:
    web:
      exposure:
        include: health,info
```

```yaml
# Deployment
readinessProbe:
  httpGet: { path: /actuator/health/readiness, port: 8080 }
  initialDelaySeconds: 10
  periodSeconds: 10
livenessProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  initialDelaySeconds: 30
  periodSeconds: 20
```

Keep the liveness check simple. If it depends on the database, a short database outage restarts
every pod at once and turns a small incident into a big one.

## 3. Shut down gracefully

During a rolling update, OpenShift sends `SIGTERM` to the old pod. Let in-flight requests finish:

```yaml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 20s
```

Set `terminationGracePeriodSeconds` on the pod higher than that timeout.

## 4. Configuration from the platform

Build **one image** and promote it through every environment. Everything that changes per
environment comes from OpenShift:

| What | Where |
|---|---|
| URLs, feature flags, log levels | `ConfigMap` as environment variables |
| Passwords, client secrets, keys | `Secret` |
| TLS for the public endpoint | `Route` with edge or re-encrypt termination |

Spring's relaxed binding maps `SPRING_DATASOURCE_URL` to `spring.datasource.url`, so no code
changes are needed.

```bash
oc create configmap orders-config --from-literal=SPRING_PROFILES_ACTIVE=prod
oc set env deployment/orders-api --from=configmap/orders-config
oc create route edge orders-api --service=orders-api
```

## 5. Set requests and limits

```yaml
resources:
  requests: { cpu: 250m, memory: 512Mi }
  limits:   { memory: 1Gi }
```

Requests let the scheduler place pods sensibly. A memory limit protects the node. I usually avoid
a tight CPU limit for JVM services because throttling slows startup and garbage collection.

## Checklist

- [x] Non-root image listening on 8080
- [x] Heap sized with `MaxRAMPercentage`
- [x] Readiness and liveness probes on Actuator
- [x] Graceful shutdown configured
- [x] Config in ConfigMaps, secrets in Secrets
- [x] Resource requests and a memory limit

Questions or feedback on this post? [Contact me](../../../portfolio/contact.md).
