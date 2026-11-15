---
title: Web SSO
description: Browser single sign-on with Keycloak in Laravel - login, silent refresh, logout and admin panels.
---

# Web SSO

The browser login uses the OpenID Connect **authorization code flow with PKCE**, through a Socialite driver.
After login the Keycloak tokens are stored in the Laravel session, and the user is logged into your
normal Laravel guard, so `auth()->user()`, `@auth` and policies work as usual.

## Protect routes

```php
Route::middleware(['web', 'keycloak.web'])->group(function () {
    Route::get('/dashboard', DashboardController::class);
});

// a specific guard (realm + client)
Route::middleware(['web', 'keycloak.web:partner-portal'])->group(/* ... */);
```

What `keycloak.web` does on every request:

1. **Guest?** It remembers the URL and redirects to the Keycloak login page. JSON requests get a `401` instead.
2. **Access token about to expire?** It refreshes the token silently with the refresh token. If Keycloak
   refuses (the session ended, the user was disabled), the user is logged out and sent back to log in.
3. Otherwise it lets the request through **without any call to Keycloak**.

## Routes

The package registers three routes (prefix and names are [configurable](configuration.md#infrastructure)):

| Route | Name | Purpose |
|---|---|---|
| `GET /auth/keycloak/login/{guard?}` | `keycloak.login` | Start the login. `?redirect=/reports` sets where to land afterwards (local URLs only). |
| `GET /auth/keycloak/callback/{guard?}` | `keycloak.callback` | OAuth callback. Register this URL in Keycloak. |
| `GET /auth/keycloak/logout/{guard?}` | `keycloak.logout` | Log out locally **and** at Keycloak, then come back. |

```blade
<a href="{{ route('keycloak.login', ['guard' => 'web']) }}">Sign in</a>
<a href="{{ route('keycloak.logout') }}">Sign out</a>
```

On the callback the package:

- exchanges the code (with the PKCE verifier) and reads the userinfo,
- creates or updates the local user from the claims ([provisioning](configuration.md#user-provisioning)),
- logs them in and **regenerates the session** to prevent session fixation,
- stores the access, refresh and ID tokens in the session,
- dispatches `UserLoggedIn`, then redirects to the remembered URL, the intended URL, or `web.home`.

A stale or replayed callback (back button, expired session, already-used code) just starts the login again.

## Logout

`keycloak.logout` uses **RP-initiated logout**: it sends `id_token_hint`, `client_id` and
`post_logout_redirect_uri`, so Keycloak ends the SSO session without a confirmation page and sends the
browser back to `redirect_after_logout`. Add that URL to *Valid post logout redirect URIs* on the client.

To end a session from the server side (for example an API logout endpoint), use the
[back-channel logout](oidc.md#logout-and-revocation): `Keycloak::oidc()->logout($refreshToken)`.

## Session validation

| `web.validation` | Cost per request | Detects a session ended in Keycloak |
|---|---|---|
| `local` *(default)* | none: compares the expiry time | at the next refresh (within the access-token lifespan, 5 minutes by default) |
| `introspect` | one cached call per `token.introspection_cache_ttl` | within the cache TTL (default 30s) |

`local` is the right choice for most apps. The 1.x version called introspection on **every** request, which
added a round-trip to Keycloak to every page view. Use `introspect` when you need near-instant
revocation, and shorten the access-token lifespan in Keycloak if you need both.

## Reading the user and the token

```php
$user  = auth()->user();            // your users model (KCUserModel by default)
$token = Keycloak::token();         // KeycloakToken from the session

$token->roles();                    // ['admin', 'editor']
$token->hasRole('admin');
$user->hasRole('admin');            // with the HasKeycloakRoles trait
session('keycloak_token');          // raw access token
```

See [Authorization](authorization.md) for every role, scope and group helper.

## Admin panels (Filament, Nova, ...)

Add the middleware to the panel's auth middleware stack:

```php
// app/Providers/Filament/AdminPanelProvider.php
->authMiddleware([
    \Bhry98\KeycloakAuth\Http\Middleware\KeycloakMiddleware::class,
])
```

and make the panel's login action point to `route('keycloak.login')`. To restrict the panel to a role,
add `canAccessPanel()` to your user model:

```php
public function canAccessPanel(Panel $panel): bool
{
    return $this->hasRole('admin'); // HasKeycloakRoles
}
```

## Several realms or clients

Each guard has its own login and callback route:

```php
'guard' => [
    'web' => [...],
    'partners' => ['realm' => 'partners', 'client_id' => 'portal', 'redirect' => env('APP_URL').'/auth/keycloak/callback/partners'],
],
```

```php
Route::middleware(['web', 'keycloak.web:partners'])->prefix('partners')->group(/* ... */);
```

Use the guard's `auth_guard` option to log each realm into a separate Laravel guard, for example
`'auth_guard' => 'partners'` with a session guard of that name in `config/auth.php`.

## Events

| Event | When |
|---|---|
| `UserLoggedIn` | after a successful callback (`$user`, `$token`, `$guard`) |
| `TokenRefreshed` | after a silent refresh (`$token`, `$guard`) |
| `UserLoggedOut` | in the logout route (`$user`, `$guard`) |
| `UserProvisioned` | when the local user row was created or changed (`$user`, `$token`, `$created`) |
