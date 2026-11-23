---
title: How-To Guides
description: Step-by-step technical guides by Abdelrahman Mahmoud. Install and configure Nginx, Git, Keycloak, Active Directory LDAPS, sync AD to Entra ID, secure Spring Boot APIs and debug OpenShift pods.
hide:
  - toc
---

<span class="bh-eyebrow">Documentation</span>

# How-To guides

<p class="bh-lead">Step-by-step guides you can follow from an empty machine to a working result.
Each guide lists its prerequisites and the commands to run, shows screenshots of what you should see,
and ends with a way to check that it worked.</p>

## Web servers &amp; proxies

<div class="grid cards" markdown>

-   :simple-nginx:{ .lg } **[How to install Nginx](nginx/install-nginx.md)**

    ---

    Install Nginx from the official repository on Ubuntu, RHEL, Docker or Windows and serve your
    first site.

    <p class="bh-chips"><code>Nginx</code><code>Linux</code><code>Docker</code></p>

-   :material-scale-balance:{ .lg } **[Nginx reverse proxy, load balancing &amp; HA](nginx/nginx-reverse-proxy-load-balancing-ha.md)**

    ---

    HTTPS reverse proxy, upstreams with failover, caching and rate limits, plus two Nginx servers
    sharing a virtual IP with keepalived.

    <p class="bh-chips"><code>Nginx</code><code>keepalived</code><code>TLS</code></p>

</div>

## Developer tools

<div class="grid cards" markdown>

-   :simple-git:{ .lg } **[How to install Git](git/install-git.md)**

    ---

    Install Git on Windows, macOS or Linux, configure it, and connect to GitHub or GitLab with an
    SSH key.

    <p class="bh-chips"><code>Git</code><code>GitHub</code><code>GitLab</code></p>

</div>

## Identity &amp; access

<div class="grid cards" markdown>

-   :material-shield-lock-outline:{ .lg } **[How to secure Active Directory with LDAPS](active-directory/enable-ldaps-active-directory.md)**

    ---

    Windows Server 2025, AD CS Enterprise CA and auto-enrolled DC certificates for
    `ldaps://` on port 636.

    <p class="bh-chips"><code>Active Directory</code><code>LDAPS</code><code>AD CS</code></p>

-   :material-microsoft-azure:{ .lg } **[How to sync Active Directory users to Entra ID](entra-id/sync-active-directory-to-entra-id.md)**

    ---

    Entra Connect Sync with password hash sync: routable UPNs, OU filtering, sync cycles and how to
    handle joiners, movers and leavers.

    <p class="bh-chips"><code>Entra ID</code><code>Active Directory</code><code>Azure</code></p>

-   :simple-keycloak:{ .lg } **[How to install Keycloak](keycloak/install-keycloak.md)**

    ---

    Run Keycloak with Docker or on Linux, connect PostgreSQL, then create your first realm,
    client and user.

    <p class="bh-chips"><code>Keycloak</code><code>Docker</code><code>PostgreSQL</code></p>

</div>

## Java &amp; Spring Boot

<div class="grid cards" markdown>

-   :simple-springboot:{ .lg } **[How to create a simple CRUD API in Spring Boot](spring-boot/simple-crud.md)**

    ---

    Build a REST API that creates, reads, updates and deletes products, with Spring Data JPA and
    validation.

    <p class="bh-chips"><code>Java</code><code>Spring Boot</code><code>JPA</code></p>

-   :simple-springsecurity:{ .lg } **[How to secure a Spring Boot API with Keycloak](spring-boot/secure-api-with-keycloak.md)**

    ---

    OAuth 2.0 resource server, JWT validation and Keycloak roles mapped to `@PreAuthorize`.

    <p class="bh-chips"><code>Spring Security</code><code>Keycloak</code><code>JWT</code></p>

</div>

## OpenShift

<div class="grid cards" markdown>

-   :simple-redhatopenshift:{ .lg } **[How to debug pods on OpenShift](openshift/debug-pods.md)**

    ---

    Pending, ImagePullBackOff, CrashLoopBackOff, OOMKilled: the `oc` commands that find the cause.

    <p class="bh-chips"><code>OpenShift</code><code>oc</code><code>Kubernetes</code></p>

</div>
