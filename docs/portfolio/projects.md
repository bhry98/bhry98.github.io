---
title: Projects
description: Selected projects by Abdelrahman (bhry98) — ERP, service desk, HR, CRM, self-service portals, AI dashboards and knowledge bases.
---

<span class="bh-eyebrow">Projects</span>

# Selected work

<p class="bh-lead">Business platforms I've designed and built. Most are private systems for organizations, so
details are kept general — I'm happy to walk you through the architecture and a demo on a call.</p>

<div class="grid cards bh-cols-4" markdown>

-   :material-office-building-cog-outline:{ .lg } **Enterprise ERP System**

    ---

    <span class="bh-tag">Enterprise</span><span class="bh-tag bh-tag--live">Production</span>

    A modular ERP that brings core business operations into one place — with department-level
    permissions, approval workflows and full audit trails.

    <p class="bh-chips"><code>Laravel</code><code>Filament</code><code>RBAC</code><code>REST API</code></p>

-   :material-face-agent:{ .lg } **Service Desk Platform**

    ---

    <span class="bh-tag">IT Operations</span>

    Ticketing with categories, priorities, SLAs, assignment and escalation rules, so support
    teams always know what to work on next.

    <p class="bh-chips"><code>Laravel</code><code>Livewire</code><code>Keycloak SSO</code></p>

-   :material-account-group-outline:{ .lg } **HR Management System**

    ---

    <span class="bh-tag">People</span>

    Employee records, leave and attendance, onboarding workflows and employee self-service
    requests.

    <p class="bh-chips"><code>Laravel</code><code>Filament</code><code>LDAP / AD</code></p>

-   :material-handshake-outline:{ .lg } **CRM**

    ---

    <span class="bh-tag">Sales</span>

    Customers, contacts, opportunities and activities in a single pipeline view, with
    reporting for managers.

    <p class="bh-chips"><code>Laravel</code><code>Livewire</code><code>MySQL</code></p>

-   :material-account-cog-outline:{ .lg } **Self-Service Portal**

    ---

    <span class="bh-tag">Employees</span>

    A single portal where users submit and track requests, reset access and find answers —
    signed in with company SSO.

    <p class="bh-chips"><code>Laravel</code><code>OpenID Connect</code><code>Keycloak</code></p>

-   :material-robot-outline:{ .lg } **AI Dashboard**

    ---

    <span class="bh-tag">Analytics</span>

    A dashboard that surfaces insights and automates routine analysis on top of business data.

    <p class="bh-chips"><code>Laravel</code><code>AI APIs</code><code>Charts</code></p>

-   :material-book-open-page-variant-outline:{ .lg } **Knowledge Base Platform**

    ---

    <span class="bh-tag">Documentation</span>

    Searchable articles, categories and permissions so teams can document processes and help
    users help themselves.

    <p class="bh-chips"><code>Laravel</code><code>Full-text search</code><code>RBAC</code></p>

-   :material-package-variant-closed:{ .lg } **Open-source Laravel packages**

    ---

    <span class="bh-tag">Open Source</span><span class="bh-tag bh-tag--live">Public</span>

    API responses, users & RBAC, Keycloak auth, dynamic enums and starter kits —
    [see all packages](packages.md).

    <p class="bh-chips"><code>PHP</code><code>Laravel 11–13</code><code>Composer</code></p>

</div>

## Typical architecture

Most of these systems share a proven foundation I can reuse for your project:

```mermaid
flowchart LR
    U[Users / Mobile app] -->|HTTPS| N[Nginx / Ingress]
    N --> A[Laravel app]
    U -.->|SSO login| K[Keycloak]
    K -.->|OIDC tokens| A
    K --- L[(LDAP / AD)]
    A --> DB[(Database)]
    A --> Q[Queue workers]
    A --> S[(MinIO / S3)]
    CI[CI/CD pipeline] -->|deploy| N
```

<div class="bh-cta" markdown>

## Want something similar?

I can build a tailored version of any of these for your organization.

[Discuss your project :material-arrow-right:](contact.md){ .md-button .md-button--primary }

</div>
