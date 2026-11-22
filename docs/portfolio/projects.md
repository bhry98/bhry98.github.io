---
title: Projects
description: Selected projects by Abdelrahman Mahmoud. ERP platform, enterprise integration, OpenShift operations and business systems.
---

<span class="bh-eyebrow">Projects</span>

# Selected work

<p class="bh-lead">Platforms I've built, integrated and operated. Most are private systems for organizations,
so details stay general. I'm happy to walk you through the architecture on a call.</p>

<div class="grid cards" markdown>

-   :material-office-building-cog-outline:{ .lg } **ERP Platform**

    ---

    <span class="bh-tag">Valleysoft</span><span class="bh-tag bh-tag--live">2024 - Present</span>

    Backend services, deployment and integration for a modular ERP. Centralized SSO with
    Keycloak, integrations with SMS providers and IoT access-control systems, and secure
    service-to-service communication.

    <p class="bh-chips"><code>Java</code><code>Spring Boot</code><code>Angular</code><code>PostgreSQL</code><code>Keycloak</code></p>

-   :material-transit-connection-variant:{ .lg } **Enterprise API &amp; Integration**

    ---

    <span class="bh-tag">Integration</span>

    API contracts, request/response transformations and secure application-to-application
    integration, connecting internal applications, ERP modules and external services.

    <p class="bh-chips"><code>IBM CP4I</code><code>App Connect</code><code>API Connect</code><code>OAuth 2.0</code></p>

-   :simple-redhatopenshift:{ .lg } **Integration Platform Operations**

    ---

    <span class="bh-tag">Platform</span>

    Administering IBM Cloud Pak for Integration environments: runtime components,
    deployments, configuration, certificates and production troubleshooting.

    <p class="bh-chips"><code>OpenShift</code><code>CP4I</code><code>Linux</code><code>GitLab CI/CD</code></p>

-   :material-shield-account-outline:{ .lg } **Centralized Identity &amp; SSO**

    ---

    <span class="bh-tag">Security</span>

    Keycloak-based single sign-on across enterprise applications, with secure authentication
    and authorization flows and LDAP integration.

    <p class="bh-chips"><code>Keycloak</code><code>OpenID Connect</code><code>LDAP</code><code>JWT</code></p>

-   :material-account-group-outline:{ .lg } **Business Modules**

    ---

    <span class="bh-tag">Valleysoft</span>

    HR, CRM, Self-Service and Service Desk modules built as part of a larger enterprise suite.

    <p class="bh-chips"><code>REST APIs</code><code>PostgreSQL</code><code>RBAC</code></p>

-   :material-gift-outline:{ .lg } **Mora Electric: Redeem Points App**

    ---

    <span class="bh-tag">Client project</span><span class="bh-tag">2025</span>

    A loyalty application that lets customers collect and redeem points.

    <p class="bh-chips"><code>Backend APIs</code><code>Integration</code></p>

</div>

## Typical architecture

Most of the systems I work on share a foundation like this:

```mermaid
flowchart LR
    U[Web / mobile clients] -->|HTTPS| G[IBM API Connect]
    G --> S[Spring Boot services]
    U -.->|SSO login| K[Keycloak]
    K -.->|OIDC tokens| S
    K --- L[(LDAP)]
    S --> DB[(PostgreSQL)]
    S <--> ACE[IBM App Connect Enterprise]
    ACE <--> X[ERP · SMS · IoT · partners]
    CI[GitLab CI/CD] -->|deploy| OCP[[Red Hat OpenShift]]
```

<div class="bh-cta" markdown>

## Questions about this work?

Curious how something here was built, or want to talk tech? Feel free to reach out.

[Contact me :material-arrow-right:](contact.md){ .md-button .md-button--primary }

</div>
