---
title: OIDC & service tokens
description: Call Keycloak's OpenID Connect endpoints from Laravel - password, refresh, client credentials, token exchange, introspection, logout - and call other services with cached tokens.
---

# OIDC & service tokens

`Keycloak::oidc($guard)` gives you the OpenID Connect / OAuth 2 endpoints of a guard's realm and client.
Token-endpoint methods return Keycloak's JSON answer as an array (`access_token`, `expires_in`,
`refresh_token`, `refresh_expires_in`, `id_token`, `token_type`, `scope`, ...).

All calls share the package's HTTP settings (timeouts, retries on connection errors, TLS verification), and
`Http::fake()` works with them in tests.

## Service-to-service calls

The most common backend need is calling another API as **this service**:

```php
use Illuminate\Support\Facades\Http;

Http::withKeycloakToken()->get('https://orders.internal/api/orders');      // default guard
Http::withKeycloakToken('api')->post('https://billing.internal/api/invoices', $data);
Http::withKeycloakToken('api', 'billing:write')->post(/* ... */);           // with a scope

$token = Keycloak::serviceToken('api');   // the raw string
```

The token is obtained with the **client credentials** grant (enable *Service accounts* on the client) and
cached until shortly before it expires (`admin.token_expiry_margin`). Every request, worker and server that
shares the cache reuses it.

To call another service **as the current user**, forward their token:

```php
Http::withKeycloakUserToken()->get('https://inventory.internal/api/stock');
```

## Token exchange

Trade the user's token for one issued to another client (RFC 8693). Token exchange must be enabled in
Keycloak.

```php
$tokens = Keycloak::oidc('api')->exchange($request->bearerToken(), audience: 'inventory-api');

Http::withToken($tokens['access_token'])->get('https://inventory.internal/api/stock');
```

## Password grant

Useful for first-party mobile apps, CLIs and tests. Requires *Direct access grants* on the client.

```php
use Bhry98\KeycloakAuth\Exceptions\OidcException;

Route::post('/api/login', function (Request $request) {
    try {
        return Keycloak::oidc('api')->password($request->input('username'), $request->input('password'));
    } catch (OidcException $e) {
        // $e->error() === 'invalid_grant', $e->errorDescription(), $e->status()
        return response()->json(['message' => 'Invalid credentials'], 401);
    }
});
```

## Refresh

```php
$tokens = Keycloak::oidc('api')->refresh($refreshToken);
```

## Client credentials, code exchange

```php
Keycloak::oidc('api')->clientCredentials('scope-a scope-b');         // uncached, full answer
Keycloak::oidc('web')->code($code, $redirectUri, $codeVerifier);     // custom frontends
```

## Introspection

Ask Keycloak whether a token is still active, for example for high-risk operations where you don't want to
wait for the token to expire:

```php
$result = Keycloak::oidc('api')->introspect($jwt);         // full RFC 7662 answer
$active = Keycloak::oidc('api')->isActive($jwt);           // cached for token.introspection_cache_ttl
```

## Userinfo

```php
$profile = Keycloak::oidc()->userInfo($accessToken);
```

## Logout and revocation

```php
Keycloak::oidc('api')->logout($refreshToken);                 // end the Keycloak session (back-channel)
Keycloak::oidc('api')->revoke($refreshToken);                 // revoke a token
Keycloak::oidc('web')->logoutUrl($idToken, url('/'));         // front-channel logout URL for browsers
```

## Discovery

```php
Keycloak::oidc()->discovery();   // .well-known/openid-configuration, cached for a day
```

## UMA permissions

See [Authorization → UMA](authorization.md#uma-permissions-authorization-services):
`checkPermission()` and `permissions()`.

## Errors

Every failure raises a `Bhry98\KeycloakAuth\Exceptions\OidcException` (a `KeycloakException`):

```php
$e->status();            // HTTP status from Keycloak (0 when unreachable)
$e->error();             // OAuth error code, e.g. "invalid_grant"
$e->errorDescription();  // human readable reason
$e->response();          // Illuminate\Http\Client\Response|null
```
