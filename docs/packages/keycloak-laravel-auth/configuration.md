---
title: Configuration
description: Every configuration option of Keycloak Laravel Auth.
---

# Configuration

All options live in `config/bhry98-keycloak.php` (publish it with `php artisan keycloak:install`). Each option
has a comment in the file. This page explains what they do.

## Guards

A **guard** is a named Keycloak *realm + client* pair. Everything in the package takes an optional guard
name: `Keycloak::oidc('api')`, `keycloak.api:api`, `Keycloak::users('web')`, `/auth/keycloak/login/web`.

```php
'default_guard' => env('KEYCLOAK_DEFAULT_GUARD', 'web'),

'guard' => [
    'web' => [
        'client_id' => env('KC_WEB_CLIENT_ID', env('KEYCLOAK_CLIENT_ID')),
        'client_secret' => env('KC_WEB_CLIENT_SECRET', env('KEYCLOAK_CLIENT_SECRET')),
        'realm' => env('KC_WEB_REALM', env('KEYCLOAK_REALM')),
        'redirect' => env('KC_WEB_REDIRECT_URI', env('KEYCLOAK_REDIRECT_URI')),
        'scopes' => ['openid', 'email', 'profile'],
    ],
    'api' => [ /* ... */ 'audience' => env('KC_API_AUDIENCE') ],
    'admin' => [ /* service account for the Admin API */ ],

    // Add as many as you need: one per frontend, tenant realm, partner...
    'partner-portal' => [
        'base_url' => 'https://sso.partner.test', // another Keycloak server
        'realm' => 'partners',
        'client_id' => 'portal',
        'client_secret' => env('PARTNER_SECRET'),
    ],
],
```

| Key | Description |
|---|---|
| `base_url` | Keycloak server URL. Defaults to the top-level `base_url`. |
| `realm`, `client_id`, `client_secret` | Realm and client credentials. Use an empty secret for public clients. |
| `redirect` | Callback URL for the browser login of this guard. |
| `scopes` | Scopes requested at login. |
| `audience` | String, comma-separated string, or array. When set, API tokens must name one of these in `aud` or `azp`. |
| `issuer` | Extra trusted issuer(s) for this guard (see [Docker & Kubernetes](api-authentication.md#docker-kubernetes-and-public-urls)). |
| `auth_guard` | The *Laravel* guard the browser login logs into (default: your default guard). |
| `redirect_after_logout` | Where Keycloak sends the browser after logout. |
| `provisioning` | `true` / `false` to override `provisioning.enabled` for this guard. |
| `role_clients` | Clients whose roles count for `hasRole()` (default: the guard's `client_id` + the token's `azp`). |

Unknown guard names fall back to the top-level `realm` / `client_id` / `client_secret`.

## Admin API

```php
'admin' => [
    'guard' => env('KEYCLOAK_ADMIN_GUARD', 'admin'), // whose credentials obtain the admin token
    'token_expiry_margin' => 30,                      // refresh admin / service tokens 30s early
],
```

The admin token is obtained once with client credentials and cached until shortly before it expires. A
`401` from the Admin API refreshes it and retries the request once.

## Token validation

```php
'token' => [
    'leeway' => 30,                     // clock-skew tolerance (seconds)
    'allowed_algs' => ['RS256', 'RS384', 'RS512', 'PS256', 'PS384', 'PS512', 'ES256', 'ES384', 'ES512', 'EdDSA'],
    'allowed_types' => ['Bearer'],      // rejects refresh and ID tokens used as access tokens
    'verify_issuer' => true,
    'issuer' => env('KEYCLOAK_ISSUER'), // public issuer when it differs from base_url
    'jwks_ttl' => 86400,                // realm public keys cache (seconds)
    'jwks_refresh_cooldown' => 30,      // min seconds between key re-downloads on unknown kid
    'introspection_cache_ttl' => 30,    // cache of introspection / UMA answers
],
```

!!! warning "Do not add `none` or `HS*` to `allowed_algs`"
    Keycloak signs access tokens with asymmetric keys. Allowing symmetric algorithms opens the door to
    algorithm-confusion attacks.

## Web SSO

```php
'web' => [
    'pkce' => true,                 // PKCE (S256) on the authorization code flow
    'validation' => 'local',        // "local" (expiry check, no network) or "introspect" (cached)
    'refresh_tokens' => true,       // silently refresh with the refresh token
    'refresh_margin' => 15,         // refresh this many seconds before expiry
    'home' => '/',                  // redirect after login when there is no intended URL
],
```

See [Web SSO → Session validation](web-sso.md#session-validation) for the trade-offs.

## User provisioning

```php
'users_model' => \Bhry98\KeycloakAuth\Models\KCUserModel::class,

'provisioning' => [
    'enabled' => env('KEYCLOAK_PROVISIONING', true),
    'sync_ttl' => 300,  // skip the DB write while the claims are unchanged
    'attributes' => [   // column => claim (dot notation, or a closure)
        'keycloak_id' => 'sub',
        'email' => 'email',
        'username' => 'preferred_username',
        'first_name' => 'given_name',
        'last_name' => 'family_name',
        'name' => 'name',
        'avatar' => 'picture',
        'locale' => 'locale',
        'email_verified' => 'email_verified',
        // 'department' => 'attributes.department',
        // 'tenant_id' => fn ($token) => Tenant::idFor($token->claim('tenant')),
    ],
],
```

Use your own model by pointing `users_model` at it. It must have the columns you map and the `keycloak_id`
column. Add the `HasKeycloakRoles` trait to it to get [role helpers](authorization.md#on-the-user-model).

!!! note "Closures in config"
    A closure in `attributes` stops `php artisan config:cache` from working. Use a custom resolver
    ([`Keycloak::resolveUserUsing()`](api-authentication.md#custom-user-resolution)) instead if you cache
    your config.

## Roles

```php
'roles' => [
    'clients' => null, // e.g. ['my-app', 'billing']; null = guard client_id + token azp
],
```

## Infrastructure

```php
'cache' => [
    'store' => env('KEYCLOAK_CACHE_STORE'), // null = default store; Redis recommended in production
    'prefix' => 'bhry98_keycloak',
],

'http' => [
    'timeout' => 10,
    'connect_timeout' => 5,
    'retries' => 2,         // connection errors only, never on 4xx/5xx answers
    'retry_delay' => 100,   // ms
    'verify' => env('KEYCLOAK_VERIFY_SSL', true),
],

'routes' => [
    'enabled' => true,
    'prefix' => 'auth/keycloak',
    'middleware' => ['web'],
    'name' => 'keycloak.',
],

'migrations' => ['auto_load' => true],
'gates' => true, // keycloak-role / keycloak-scope gates and the @keycloakRole directive
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `KEYCLOAK_BASE_URL` | – | Keycloak server URL |
| `KEYCLOAK_REALM` | – | Default realm |
| `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_CLIENT_SECRET` | – | Default client |
| `KEYCLOAK_REDIRECT_URI` | `/auth/keycloak/callback` | Default login callback |
| `KEYCLOAK_RED_AFTER_LOGOUT` | `APP_URL` | Post-logout redirect |
| `KEYCLOAK_DEFAULT_GUARD` | `web` | Guard used when none is given |
| `KC_{WEB,API,ADMIN}_{CLIENT_ID,CLIENT_SECRET,REALM,REDIRECT_URI}` | defaults above | Per-guard overrides |
| `KC_API_AUDIENCE` | – | Required audience for API tokens |
| `KEYCLOAK_ADMIN_GUARD` | `admin` | Credentials used for the Admin API |
| `KEYCLOAK_ISSUER` | – | Public issuer URL |
| `KEYCLOAK_VERIFY_ISSUER` | `true` | Check `iss` |
| `KEYCLOAK_TOKEN_LEEWAY` | `30` | Clock skew (seconds) |
| `KEYCLOAK_JWKS_TTL` | `86400` | Realm keys cache (seconds) |
| `KEYCLOAK_PKCE` | `true` | PKCE on browser login |
| `KEYCLOAK_WEB_VALIDATION` | `local` | `local` or `introspect` |
| `KEYCLOAK_HOME` | `/` | Redirect after login |
| `KEYCLOAK_PROVISIONING` | `true` | Sync users to the database |
| `KEYCLOAK_CACHE_STORE` | default | Cache store |
| `KEYCLOAK_VERIFY_SSL` | `true` | TLS verification |
