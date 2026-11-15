---
title: API authentication
description: Protect Laravel APIs and microservices with Keycloak bearer tokens, verified offline.
---

# API authentication

Your SPA, mobile app or another service gets an access token from Keycloak and sends it as
`Authorization: Bearer <token>`. The package **verifies the token offline** against the realm's cached
public keys. A request needs no call to Keycloak and no database query, unless you
[provision users](#users-stateless-or-database).

There are two ways to plug it in. Both share the same validation, caching and user resolution.

## Option 1: the `keycloak.api` middleware

```php
// routes/api.php
Route::middleware('keycloak.api')->group(function () {
    Route::get('/me', fn (Request $request) => $request->user());
    Route::apiResource('orders', OrderController::class);
});

Route::middleware('keycloak.api:partners')->group(/* tokens of the "partners" guard */);
```

When nothing is passed it uses the `api` guard if you configured one, otherwise the default guard.

Failures return JSON:

```json
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer

{ "error": "Invalid or expired token" }
```

With `APP_DEBUG=true` the response also contains a `message` with the exact reason (expired, wrong issuer,
audience...).

## Option 2: the `keycloak` auth guard

Register a guard in `config/auth.php`:

```php
'guards' => [
    'web' => ['driver' => 'session', 'provider' => 'users'],

    'api' => [
        'driver' => 'keycloak',
        'keycloak' => 'api',      // which package guard (realm + client) to verify against
        // 'provision' => false,  // override provisioning for this guard
    ],
],
```

Then use Laravel's own `auth` middleware and helpers:

```php
Route::middleware('auth:api')->get('/me', fn () => auth('api')->user());

auth('api')->check();
auth('api')->id();                        // Keycloak subject (stateless) or local id
auth('api')->token();                     // KeycloakToken
auth('api')->hasRole('admin');
auth('api')->validate(['token' => $jwt]); // check without logging in
```

Unauthenticated requests go through Laravel's normal `AuthenticationException` handling (JSON `401` for API
requests). The guard is safe for **Laravel Octane**: it is reset for every request.

## Users: stateless or database

=== "Stateless (no database)"

    ```env
    KEYCLOAK_PROVISIONING=false
    ```

    `$request->user()` is a `Bhry98\KeycloakAuth\Auth\KeycloakUser` built from the token claims. This is
    the fastest option and fits microservices that don't own user data.

    ```php
    $user = $request->user();
    $user->id;                 // "sub"
    $user->email;
    $user->preferred_username; // any claim is readable as a property
    $user->hasRole('admin');
    $user->token();            // KeycloakToken
    ```

=== "Provisioned (database row)"

    ```env
    KEYCLOAK_PROVISIONING=true   # default
    ```

    The local user (your `users_model`) is created on the first request and updated when the claims
    change. While the claims stay the same, the write is skipped for `provisioning.sync_ttl` seconds, so a
    hot request costs a single primary-key lookup. Existing rows with the same e-mail are adopted.

    Map extra claims to columns with [`provisioning.attributes`](configuration.md#user-provisioning).

**Service accounts** (client-credentials tokens) are never written to the database. They always
resolve to a `KeycloakUser`, so machine clients work even with provisioning on.

### Custom user resolution

Take full control over how a token becomes a user, for example to look up a tenant or deny unknown users:

```php
// AppServiceProvider::boot()
use Bhry98\KeycloakAuth\Facades\Keycloak;
use Bhry98\KeycloakAuth\Token\KeycloakToken;

Keycloak::resolveUserUsing(function (KeycloakToken $token, string $guard) {
    return User::firstWhere('keycloak_id', $token->subject()); // null = unauthenticated
});
```

## Reading the token

```php
use Bhry98\KeycloakAuth\Facades\Keycloak;

$token = Keycloak::token();     // current request token (or inject KeycloakToken)

$token->subject();              // user id
$token->email();
$token->username();
$token->azp();                  // client the token was issued to
$token->roles();                // realm + guard-client roles
$token->scopes();
$token->groups();
$token->expiresAt();            // CarbonImmutable
$token->claim('tenant.id');     // any claim, dot notation
$token->jwt();                  // raw token, e.g. to forward it
```

```php
public function index(KeycloakToken $token) { /* injected from the container */ }
```

## Validating tokens yourself

For queues, WebSockets, gRPC or anywhere outside HTTP middleware:

```php
$token = Keycloak::validate($jwt, 'api');   // throws TokenValidationException
$token = Keycloak::check($jwt, 'api');      // or returns null
$token = Keycloak::decode($jwt);            // claims only, NO verification
```

What is verified:

- **Signature** against the realm's JWKS, with only [allow-listed algorithms](configuration.md#token-validation).
- **Expiry and not-before**, with `token.leeway` seconds of clock skew.
- **Issuer**: `{base_url}/realms/{realm}` or a configured public issuer.
- **Audience**: when the guard has `audience`, it must be in `aud` or `azp`.
- **Type**: `typ` must be `Bearer`, so refresh and ID tokens are refused.

## Performance notes

- Realm keys are cached in your cache store (`token.jwks_ttl`, 1 day) **and** memoized in-process.
- When a token is signed with an **unknown key id** (Keycloak rotated its keys), the keys are downloaded
  again, at most once per `token.jwks_refresh_cooldown` seconds. Forged tokens can't be used to flood
  Keycloak with requests.
- The same token is verified only once per process (up to 256 recent tokens are memoized; the expiry is
  re-checked on every use).
- Use a shared cache (Redis) in production so every server and worker reuses the same keys and tokens.

## Docker, Kubernetes and public URLs

Inside a cluster your app often reaches Keycloak at an internal URL (`http://keycloak:8080`), while tokens
are issued with the **public** URL as `iss` (`https://sso.example.com/realms/my-realm`). Keep the internal
URL for HTTP calls and trust the public issuer:

```env
KEYCLOAK_BASE_URL=http://keycloak:8080
KEYCLOAK_ISSUER=https://sso.example.com    # realm path is added automatically
```

You can also set `issuer` per guard (string or array) in the config.

## Microservices

A typical setup: each service verifies incoming tokens with `keycloak.api`, and calls other services either
on behalf of the **user** (forward the token) or as **itself** (service account):

```php
// forward the caller's token
Http::withKeycloakUserToken()->get('http://inventory/api/stock');

// call as this service (client credentials, cached until it expires)
Http::withKeycloakToken('api')->post('http://billing/api/invoices', $payload);
```

See [OIDC & service tokens](oidc.md) for token exchange and scopes.

## Events

| Event | When |
|---|---|
| `TokenValidated` | a bearer token was accepted (`$token`, `$guard`) |
| `TokenValidationFailed` | a bearer token was rejected (`$exception`, `$guard`, `$request`), useful for auditing and alerts |
| `UserProvisioned` | the local user row was created or changed |
