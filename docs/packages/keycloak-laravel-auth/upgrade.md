---
title: Upgrade guide
description: Upgrading Keycloak Laravel Auth from 1.x to 2.x, and the full changelog.
---

# Upgrade guide

## From 1.x to 2.0

2.0 is a rewrite, but the **1.x public API keeps working**: config keys, routes, middleware aliases,
`KCAuth`, `KCUserModel`, and the `KeycloakUsersService`, `KeycloakRoleService`, `KeycloakGroupService` and
`KeycloakJWTService` classes.

```bash
composer require bhry98/keycloak-laravel-auth:^2.0
php artisan migrate          # safe to run; nothing changes for existing 1.x tables
php artisan keycloak:check
```

### Requirements

- PHP **8.2+** and Laravel **11, 12 or 13**.
- `creativeorange/gravatar` is no longer required. `avatar_url` builds the Gravatar URL itself. Remove the
  package if nothing else uses it.

### Behaviour changes to review

| Area | 1.x | 2.0 | What to do |
|---|---|---|---|
| `keycloak.web` | introspection call to Keycloak on **every** request | local expiry check + silent refresh | Nothing. Set `KEYCLOAK_WEB_VALIDATION=introspect` to keep server-side checks (now cached). |
| `keycloak.api` | verified the token, `$request->user()` was empty | also resolves the user (provisioned or stateless) | Set `KEYCLOAK_PROVISIONING=false` to keep APIs database-free. |
| `keycloak.api` failure body | `{"error": "..."}` | same, plus `message` when `APP_DEBUG=true` | none |
| Logout | redirected to Keycloak, user stayed there | RP-initiated logout, user returns to `redirect_after_logout` | Add the URL to *Valid post logout redirect URIs*. |
| Login | no PKCE | PKCE (S256) | none (`KEYCLOAK_PKCE=false` to disable) |
| Invalid OAuth state | `Cache::clear()` (wiped the whole app cache!) | restarts the login | none |
| `VerifyKeycloakTokenForAgent` | `Auth::login()` + session write per request | sets the user for the request only | none |
| `KeycloakRoleService::guard('x')` | managed the admin realm | manages realm `x` (no `guard()` call → admin realm, as before) | Check calls that relied on the bug. |
| `KeycloakGroupService::createGroup()` | crashed (`dd()`) | returns `true` | none |
| Admin token | cached 55 seconds | cached for its real lifetime, refreshed on 401 | none |
| Users migration | failed when `users` already existed | adds the missing columns | none |
| Users migration `down()` | dropped `users` | no-op (never drops your users table) | none |

### Recommended (optional) changes

```php
// Before
$jwt = (new KeycloakJWTService)->validateAndDecode($token);
$roles = KCAuth::userRoles();
(new KeycloakRoleService)->assignRoleToUser($userId, 'editor');

// After
$token = Keycloak::check($token, 'api');
$roles = Keycloak::token()->roles();
Keycloak::users()->assignRealmRoles($userId, ['editor']);
```

- Use the [`keycloak` auth guard](api-authentication.md#option-2-the-keycloak-auth-guard) for APIs.
- Replace `VerifyKeycloakTokenForAgent` / `VerifyKeycloakTokenForApiAgent` with `keycloak.api`.
- Replace hand-written `Http::withToken(...)` service calls with
  [`Http::withKeycloakToken()`](oidc.md#service-to-service-calls).
- Use [`actingAsKeycloakUser()`](testing.md) in your tests.

## Changelog

### 2.0.0

**Added**

- `Keycloak` facade / `KeycloakManager` as the single entry point.
- `keycloak` auth-guard driver; stateless `KeycloakUser`; `HasKeycloakRoles` trait.
- Offline JWT verification with cached JWKS, key-rotation handling, issuer / audience / type / algorithm checks.
- `keycloak.role`, `keycloak.roles`, `keycloak.scope`, `keycloak.permission` middleware; gates; Blade directives.
- OIDC client: password, refresh, client credentials, code, token exchange, introspection, userinfo, logout,
  revoke, discovery, UMA permissions.
- Cached service tokens, `Http::withKeycloakToken()` and `Http::withKeycloakUserToken()`.
- Admin API: users, realm roles, groups, clients and client roles, realm events, lazy pagination.
- `keycloak:install`, `keycloak:check`, `keycloak:decode`, `keycloak:clear-cache`.
- Events, testing helpers, PKCE, configurable routes / cache / HTTP, Laravel 11–13 support, CI.

**Fixed**

- Leftover `dd()` calls in the role and group services.
- Missing `firebase/php-jwt` requirement.
- Wrong certificates URL in `VerifyKeycloakTokenForApiAgent`.
- `Cache::clear()` on invalid OAuth state.
- Role service targeting the wrong realm.
- Session fixation after login.

### 1.0.0

First release: Socialite login, `keycloak.web` / `keycloak.api` middleware, users / roles / groups services.
