---
date: 2026-09-15
slug: laravel-on-kubernetes-openshift
authors:
  - bhry98
categories:
  - DevOps
  - Laravel
description: A production-ready approach to running Laravel on Kubernetes and OpenShift — images, health checks, queues, scheduler and migrations.
---

# Shipping Laravel to Kubernetes & OpenShift

"It works on my machine" isn't a deployment strategy. Running Laravel on Kubernetes or OpenShift
gives you repeatable releases, self-healing and easy scaling — as long as you design the app for it.
Here's the checklist I follow.

<!-- more -->

## 1. Treat the app as stateless

Pods are disposable and there will be more than one of them. So:

| Concern | Don't | Do |
|---|---|---|
| Sessions & cache | `file` driver | Redis (or the database) |
| Uploads | `storage/app` on the pod | S3-compatible storage such as MinIO |
| Logs | `storage/logs/*.log` | `LOG_CHANNEL=stderr` — the platform collects them |
| Config | `.env` baked into the image | ConfigMaps & Secrets as environment variables |

## 2. Build a lean, non-root image

OpenShift runs containers with a **random user ID** that belongs to the root *group*. If your image
assumes it runs as root, or writes to directories only its owner can write to, it will crash.
Two rules cover it: listen on a port above 1024, and make writable paths group-writable.

```dockerfile
# --- dependencies ---
FROM composer:2 AS vendor
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --prefer-dist --no-interaction
COPY . .
RUN composer dump-autoload --optimize --classmap-authoritative

# --- runtime ---
FROM php:8.3-apache
RUN docker-php-ext-install pdo_mysql opcache \
 && a2enmod rewrite

ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
 && sed -ri 's/Listen 80/Listen 8080/' /etc/apache2/ports.conf \
 && sed -ri 's/:80>/:8080>/' /etc/apache2/sites-available/000-default.conf

WORKDIR /var/www/html
COPY --from=vendor /app .

# writable by any UID in group 0 (OpenShift-friendly)
RUN chgrp -R 0 storage bootstrap/cache /var/run/apache2 /var/lock/apache2 /var/log/apache2 \
 && chmod -R g=u storage bootstrap/cache /var/run/apache2 /var/lock/apache2 /var/log/apache2

USER 1001
EXPOSE 8080
```

!!! tip
    Run `php artisan config:cache` and `route:cache` when the container **starts**, not at build
    time — configuration comes from the environment, which differs per cluster.

## 3. Health checks

Laravel 11+ ships a `/up` health route out of the box. Use it for both probes:

```yaml
readinessProbe:
  httpGet: { path: /up, port: 8080 }
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet: { path: /up, port: 8080 }
  initialDelaySeconds: 20
  periodSeconds: 20
```

A failing readiness probe takes the pod out of the load balancer; a failing liveness probe
restarts it.

## 4. One image, several workloads

The same image runs every part of the application — only the command changes:

| Workload | Kubernetes object | Command |
|---|---|---|
| Web | `Deployment` + `Service` + `Ingress`/`Route` | default (Apache) |
| Queue workers | `Deployment` (scale independently) | `php artisan queue:work --tries=3` |
| Scheduler | `Deployment` with 1 replica | `php artisan schedule:work` |
| Migrations | `Job` run by the pipeline before rollout | `php artisan migrate --force` |

Running migrations as a **separate Job** avoids several web pods racing to migrate at once.

## 5. Zero-downtime releases

- Use a `RollingUpdate` strategy with `maxUnavailable: 0`.
- Keep migrations **backwards compatible** for one release: add columns first, remove them later.
- Let workers finish their current job: set `terminationGracePeriodSeconds` higher than your longest
  job, and Laravel's worker will stop gracefully on `SIGTERM`.

## 6. Automate it

A typical GitHub Actions / GitLab CI pipeline:

```mermaid
flowchart LR
    A[Push] --> B[Tests & static analysis]
    B --> C[Build & push image]
    C --> D[Run migration Job]
    D --> E[Rolling update]
    E --> F[Smoke test /up]
```

Every release becomes boring — and boring is exactly what production should be.

Planning a move to containers? [I can help](../../portfolio/services.md).
