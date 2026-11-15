---
title: Installation
description: Install Keycloak Laravel Auth, configure your .env and set up the Keycloak clients.
---

# Installation

## Requirements

| | |
|---|---|
| PHP | 8.2 or newer, with `ext-openssl` and `ext-json` |
| Laravel | 11.x, 12.x or 13.x |
| Keycloak | 17 or newer (URLs without `/auth`). For older servers, put `/auth` in `KEYCLOAK_BASE_URL`. |

## Install via Composer

```bash
composer require bhry98/keycloak-laravel-auth
```

The service provider and the `Keycloak` facade are auto-discovered.

```bash
php artisan keycloak:install      # publishes config/bhry98-keycloak.php and prints the .env keys
php artisan migrate               # adds the Keycloak columns to your users table
```

!!! info "Users table"
    The bundled migration **creates** a `users` table, or, if your app already has one (Laravel's default
    migration), **adds** the Keycloak columns (`keycloak_id`, `keycloak_realm`, `username`, ...) and makes
    `password` nullable. To customise it, set `migrations.auto_load` to `false` and publish it:
    `php artisan vendor:publish --tag=bhry98-keycloak-migrations`.

    You only need the table if you use the [browser login](web-sso.md) or
    [user provisioning](api-authentication.md#users-stateless-or-database). A pure API that uses
    stateless users needs no table at all.

## Environment

The minimum for one realm and one client:

```env
KEYCLOAK_BASE_URL=https://sso.example.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-laravel-app
KEYCLOAK_CLIENT_SECRET=change-me
KEYCLOAK_REDIRECT_URI="${APP_URL}/auth/keycloak/callback/web"
```

Every guard (`web`, `api`, `admin`) falls back to these values. Override them per guard when you use different
clients:

```env
# Browser login client
KC_WEB_CLIENT_ID=my-web-app
KC_WEB_CLIENT_SECRET=...

# API resource server: tokens must be issued for this audience
KC_API_CLIENT_ID=orders-api
KC_API_AUDIENCE=orders-api

# Admin REST API service account (can live in another realm)
KC_ADMIN_REALM=my-realm
KC_ADMIN_CLIENT_ID=laravel-admin
KC_ADMIN_CLIENT_SECRET=...
```

Then check everything is reachable:

```bash
php artisan keycloak:check --admin
```

```text
+-------+----------+----------------+------------------------------------------+-------------------+--------------------+
| Guard | Realm    | Client         | Discovery                                | JWKS              | Client credentials |
+-------+----------+----------------+------------------------------------------+-------------------+--------------------+
| web   | my-realm | my-web-app     | https://sso.example.com/realms/my-realm  | 1 signing key(s)  | ok                 |
| api   | my-realm | orders-api     | https://sso.example.com/realms/my-realm  | 1 signing key(s)  | ok                 |
| admin | my-realm | laravel-admin  | https://sso.example.com/realms/my-realm  | 1 signing key(s)  | ok                 |
+-------+----------+----------------+------------------------------------------+-------------------+--------------------+
Admin API token: ok
```

## Setting up Keycloak

Create the clients in your realm (**Clients → Create client**, type *OpenID Connect*).

=== "Browser login (web)"

    | Setting | Value |
    |---|---|
    | Client authentication | **On** (confidential) |
    | Standard flow | **On** |
    | Valid redirect URIs | `https://your-app.test/auth/keycloak/callback/web` |
    | Valid post logout redirect URIs | `https://your-app.test/*` (or `+`) |
    | Web origins | `https://your-app.test` |
    | Advanced → PKCE method | `S256` (optional, the package always sends it) |

=== "API (resource server)"

    The API only **verifies** tokens, so it needs no flow enabled. To require that tokens are meant for
    your API, add an **Audience** mapper to the client that *issues* the tokens (your SPA / mobile app):

    1. *Client scopes → Create* `orders-api-audience` → *Mappers → By configuration → Audience*,
       included client audience: `orders-api`.
    2. Add the scope to the SPA client as a *Default* scope.
    3. Set `KC_API_AUDIENCE=orders-api`.

    Enable **Service accounts** on this client if it also calls other services with
    [`Http::withKeycloakToken()`](oidc.md#service-to-service-calls).

=== "Admin API (service account)"

    | Setting | Value |
    |---|---|
    | Client authentication | **On** |
    | Standard flow | Off |
    | Service accounts roles | **On** |

    Then in **Service account roles → Assign role → Filter by clients**, add the `realm-management`
    roles you need, for example `manage-users`, `view-users`, `query-groups`, `view-clients` or
    `manage-realm`.

=== "Password grant (optional)"

    For [`Keycloak::oidc()->password()`](oidc.md#password-grant), enable **Direct access grants** on the
    client. Prefer the browser flow for user-facing apps. The password grant is mainly useful for
    first-party mobile apps, CLIs and tests.

## Roles, groups and scopes in the token

Keycloak puts realm roles in `realm_access.roles` and client roles in `resource_access.<client>.roles` by
default (the *roles* client scope). For groups, add a **Group Membership** mapper (token claim name `groups`,
*Full group path* on) to a client scope. See [Authorization](authorization.md).

## Next

- Browser app or admin panel: [Web SSO](web-sso.md)
- REST API or microservice: [API authentication](api-authentication.md)
- Fine-tune behaviour: [Configuration](configuration.md)
