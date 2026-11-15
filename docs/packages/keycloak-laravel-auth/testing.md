---
title: Testing & tooling
description: Test Keycloak-protected Laravel apps without a Keycloak server, plus Artisan commands and events.
---

# Testing & tooling

## Testing your application

`Keycloak::fake()` generates a local RSA key pair, makes every configured guard trust it, and signs real
RS256 tokens. Your middleware, guards, role checks and provisioning run exactly as in production, and no
Keycloak server is needed.

Add the trait to your base `TestCase`:

```php
use Bhry98\KeycloakAuth\Testing\InteractsWithKeycloak;

abstract class TestCase extends BaseTestCase
{
    use InteractsWithKeycloak;
}
```

### API routes

```php
it('lists orders for managers', function () {
    $this->actingAsKeycloakUser(['roles' => ['manager']])
        ->getJson('/api/orders')
        ->assertOk();
});

it('forbids plain users', function () {
    $this->actingAsKeycloakUser(['roles' => ['user']])
        ->getJson('/api/orders')
        ->assertForbidden();
});

it('needs a token', function () {
    $this->getJson('/api/orders')->assertUnauthorized();
});
```

Claim shortcuts:

| Key | Becomes |
|---|---|
| `roles` | `realm_access.roles` |
| `client_roles` | `['editor']` → roles of the guard client, or `['billing' => ['viewer']]` |
| `scopes` | the space-separated `scope` claim |
| anything else | copied as-is (`sub`, `email`, `groups`, `tenant`, ...); `null` removes a default claim |

Defaults include a random `sub`, `email`, `preferred_username`, names, `typ: Bearer`, the guard's client as
`azp`, the correct `iss` and a 5-minute expiry.

```php
$jwt = $this->keycloakToken(['sub' => $user->keycloak_id], guard: 'api');

$fake = Keycloak::fake();
$fake->token(['roles' => ['admin']], 'api', ttl: -60);  // an expired token
$fake->make([...]);                                    // a KeycloakToken object
$fake->tokenResponse([...]);                           // a token-endpoint style array
$fake->jwks();                                         // the public keys
```

### Web routes

```php
it('shows the dashboard', function () {
    $user = User::factory()->create(['keycloak_id' => (string) Str::uuid()]);

    $this->actingAsKeycloakWebUser($user, ['roles' => ['admin']])
        ->get('/dashboard')
        ->assertOk();
});
```

### Keycloak HTTP calls

OIDC and Admin API calls go through Laravel's HTTP client, so `Http::fake()` works:

```php
Http::fake([
    '*/realms/master/protocol/openid-connect/token' => Http::response(['access_token' => 'x', 'expires_in' => 60]),
    '*/admin/realms/my-realm/users' => Http::response(null, 201, ['Location' => '.../users/new-id']),
]);

expect(Keycloak::users()->create(['username' => 'jane']))->toBe('new-id');
```

## Artisan commands

| Command | What it does |
|---|---|
| `keycloak:install [--migrations]` | Publish the config (and migrations) and print the `.env` keys. |
| `keycloak:check [guard...] [--admin]` | For each guard: discovery document, realm keys, client credentials, and optionally an Admin API token. Exits non-zero on failure, which makes it usable as a deploy or readiness check. |
| `keycloak:decode {token} [--guard=] [--verify]` | Print subject, client, issuer, expiry, roles, scopes and all claims; `--verify` also checks signature, expiry, issuer and audience. |
| `keycloak:clear-cache` | Forget cached realm keys, discovery documents, admin and service tokens. |

```bash
php artisan keycloak:decode eyJhbGciOiJSUzI1NiIs... --guard=api --verify
```

## Events

| Event | Payload | Typical use |
|---|---|---|
| `TokenValidated` | `$token`, `$guard` | metrics, tenant context |
| `TokenValidationFailed` | `$exception`, `$guard`, `$request` | audit log, alerting on forged tokens |
| `UserLoggedIn` | `$user`, `$token`, `$guard` | last-login timestamp, welcome flow |
| `UserLoggedOut` | `$user`, `$guard` | audit log |
| `TokenRefreshed` | `$token`, `$guard` | refresh cached permissions |
| `UserProvisioned` | `$user`, `$token`, `$created` | sync roles / teams, welcome e-mail on `$created` |

```php
Event::listen(UserProvisioned::class, function (UserProvisioned $event) {
    if ($event->created) {
        Mail::to($event->user)->queue(new Welcome);
    }
});
```

All events live in `Bhry98\KeycloakAuth\Events`.

## Long-running workers (Octane, queues)

The package keeps resolved config, realm keys and recently verified tokens in memory for speed. The
`keycloak` guard is reset for every request. After changing config at runtime, call:

```php
Keycloak::forgetResolved();   // drop in-memory state
Keycloak::flushCache();       // also forget cached keys and tokens
```
