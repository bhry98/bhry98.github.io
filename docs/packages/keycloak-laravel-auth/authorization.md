---
title: Authorization
description: Keycloak roles, client roles, scopes, groups and UMA permissions in Laravel middleware, gates, Blade and models.
---

# Authorization

All checks read the **current request's token**: the verified bearer token on API routes, or the session
token on web routes. They make no network call, except [UMA permissions](#uma-permissions-authorization-services).

## Role semantics

| You write | Matches |
|---|---|
| `admin` | the realm role `admin` **or** the role `admin` of the guard's client (and of the token's `azp`) |
| `billing:invoice-viewer` | the role `invoice-viewer` of the client `billing` |
| `App\Enums\Role::Admin` | backed enums use their value, pure enums their name |

The "guard's client" can be changed with `roles.clients` or the guard's `role_clients`
([configuration](configuration.md#roles)).

## Middleware

```php
// at least one of the roles
Route::middleware(['keycloak.api', 'keycloak.role:admin,editor'])->group(/* ... */);

// all of the roles
Route::middleware(['keycloak.api', 'keycloak.roles:admin,auditor'])->group(/* ... */);

// client role
Route::middleware(['keycloak.api', 'keycloak.role:billing:invoice-viewer'])->get('/invoices', /* ... */);

// at least one of the scopes
Route::middleware(['keycloak.api', 'keycloak.scope:orders:read,orders:write'])->get('/orders', /* ... */);

// Keycloak Authorization Services (UMA), all listed permissions
Route::middleware(['keycloak.api', 'keycloak.permission:invoice#read'])->get('/invoices/{id}', /* ... */);
```

They work after `keycloak.api`, `keycloak.web` or `auth:<keycloak guard>`. Without a token they respond
with `401`, without the role/scope with `403`.

## In code

```php
use Bhry98\KeycloakAuth\Facades\Keycloak;

$token = Keycloak::token();

$token->hasRole('admin');
$token->hasAnyRole(['admin', 'editor']);
$token->hasAllRoles(['admin', 'auditor']);
$token->hasRealmRole('offline_access');
$token->hasClientRole('invoice-viewer', 'billing');

$token->realmRoles();            // ['admin', 'offline_access', ...]
$token->clientRoles();           // roles of the guard client(s)
$token->clientRoles('billing');
$token->allClientRoles();        // ['billing' => [...], 'account' => [...]]

$token->scopes();                // ['openid', 'email', 'orders:read']
$token->hasScope('orders:read');
$token->hasAnyScope(['a', 'b']);

$token->groups();                // ['/company/engineering']
$token->inGroup('engineering');  // matches "/company/engineering"
```

## Gates and policies

The package registers these abilities (disable with `'gates' => false`):

| Ability | Arguments |
|---|---|
| `keycloak-role` | one or more roles (any) |
| `keycloak-roles` | one or more roles (all) |
| `keycloak-scope` | one or more scopes (any) |
| `keycloak-group` | a group name or path |

```php
Gate::allows('keycloak-role', 'admin');
Gate::authorize('keycloak-role', ['admin', 'editor']);
$this->authorize('keycloak-scope', 'orders:write');   // in a controller
```

```blade
@can('keycloak-role', 'admin')
    <a href="/admin">Admin</a>
@endcan
```

!!! note "`can:` middleware"
    Laravel's `can:ability,arg` middleware reads its arguments as **route parameters or model classes**, not
    as plain strings. Use `keycloak.role:...` for routes, and the gates in code and Blade.

Inside your own policies, use the token directly:

```php
public function update(User $user, Invoice $invoice): bool
{
    return $user->hasRole('billing:invoice-editor') && $invoice->tenant_id === $user->tenant_id;
}
```

## Blade directives

```blade
@keycloakRole('admin', 'editor')
    <button>Publish</button>
@endkeycloakRole

@keycloakScope('orders:write')
    <button>New order</button>
@endkeycloakScope
```

## On the user model

Add `HasKeycloakRoles` to your user model (the bundled `KCUserModel` already has it):

```php
use Bhry98\KeycloakAuth\Concerns\HasKeycloakRoles;

class User extends Authenticatable
{
    use HasKeycloakRoles;
}
```

```php
$user->hasRole('admin');
$user->hasAnyRole(['admin', 'editor']);
$user->hasAllRoles([...]);
$user->hasRealmRole('...');
$user->hasClientRole('viewer', 'billing');
$user->hasScope('orders:read');
$user->inGroup('engineering');
$user->keycloakRoles();       // ['admin', ...]
$user->keycloakGroups();
$user->keycloakToken();       // KeycloakToken, or null when the current token belongs to someone else
```

The helpers only answer `true` when the current token belongs to **this** user (matched by
`keycloak_id`), so checking roles of another user model returns `false` instead of leaking the caller's
roles.

Stateless API users (`KeycloakUser`) have the same methods.

## UMA permissions (Authorization Services)

If you model resources, scopes and policies in Keycloak (*Client → Authorization* tab), ask Keycloak
for a decision:

```php
$oidc = Keycloak::oidc('api');

$oidc->checkPermission($token->jwt(), 'invoice#read');               // resource#scope
$oidc->checkPermission($token->jwt(), ['invoice#read', 'report']);   // all of them
$oidc->permissions($token->jwt());   // [['rsname' => 'invoice', 'scopes' => ['read']], ...]
```

Decisions are cached for `token.introspection_cache_ttl` seconds (default 30s) per token and permission set.
The audience defaults to the guard's `client_id` (the resource server).

## 1.x `KCAuth` facade

The 1.x helpers still work and now read the current token:

```php
use Bhry98\KeycloakAuth\Facades\KCAuth;

KCAuth::userRoles();
KCAuth::userRealmRoles();
KCAuth::userClientRoles();
KCAuth::hasAccess(['admin', Role::Editor]);
KCAuth::hasAccess(['editor'], inClientRoleOnly: true);
```
