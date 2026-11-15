---
title: Admin API
description: Manage Keycloak users, roles, groups and clients from Laravel with the Admin REST API client.
---

# Admin API

`Keycloak::admin($guard)` is a client for the Keycloak **Admin REST API** of a guard's realm. It
authenticates with the service account of the `admin` guard (see
[Installation → Setting up Keycloak](installation.md#setting-up-keycloak)).

```php
use Bhry98\KeycloakAuth\Facades\Keycloak;

Keycloak::users();          // = Keycloak::admin()->users(), default guard's realm
Keycloak::users('partners');// another realm
Keycloak::roles();
Keycloak::groups();
Keycloak::clients();
Keycloak::admin()->realm();
```

- The admin token is fetched once, **cached for its real lifetime** and shared by all calls. A `401` refreshes
  it and retries once.
- Methods return Keycloak's JSON representations as plain arrays.
- Failures throw `Bhry98\KeycloakAuth\Exceptions\AdminApiException` (`status()`, `errorDescription()`,
  `response()`). `find()`-style methods return `null` on `404`.
- Client UUID lookups are cached, so you always pass the human `clientId` (`"billing"`), never the UUID.

## Users

```php
$users = Keycloak::users();

// Create: snake_case or Keycloak camelCase keys. Returns the new id.
$id = $users->create([
    'username' => 'jane',
    'email' => 'jane@example.com',
    'first_name' => 'Jane',
    'last_name' => 'Doe',
    'email_verified' => true,
    'enabled' => true,                      // default true
    'attributes' => ['department' => 'IT'], // values become arrays
    'groups' => ['/staff'],
    'required_actions' => ['VERIFY_EMAIL'],
    'password' => 'S3cret!',
    'temp_password' => true,                // force a change at first login
]);

$users->update($id, ['first_name' => 'Janet']);  // partial update
$users->setAttributes($id, ['department' => 'HR', 'legacy_id' => null]); // merge; null removes
$users->disable($id);
$users->enable($id);
$users->resetPassword($id, 'N3w-pass', temporary: false);
$users->delete($id);
```

### Finding users

```php
$users->find($id);                     // array|null
$users->findOrFail($id);
$users->findByEmail('jane@example.com');
$users->findByUsername('jane');
$users->findByAttribute('employee_id', '42');
$users->search('jan', first: 0, max: 20);
$users->all(['enabled' => 'true', 'briefRepresentation' => 'true', 'max' => 50]);
$users->count(['emailVerified' => 'true']);

// Walk every user without loading them all at once (LazyCollection, pages of 100)
$users->cursor()->each(fn (array $user) => SyncUser::dispatch($user));
```

### E-mails and required actions

```php
$users->sendVerifyEmail($id);
$users->sendResetPasswordEmail($id, lifespan: 3600, redirectUri: 'https://app.test/login');
$users->executeActionsEmail($id, ['UPDATE_PASSWORD', 'CONFIGURE_TOTP']);
```

### Sessions and credentials

```php
$users->sessions($id);
$users->logout($id);                   // sign out of every session
$users->credentials($id);
$users->deleteCredential($id, $credentialId);   // e.g. reset OTP
$users->federatedIdentities($id);      // linked Google / GitHub / LDAP accounts
```

### Groups and roles of a user

```php
$users->groups($id);
$users->joinGroup($id, $groupId);
$users->leaveGroup($id, $groupId);

$users->realmRoles($id);                         // direct
$users->realmRoles($id, effective: true);        // including composites & groups
$users->realmRoleNames($id);                     // ['admin', ...] (effective)
$users->assignRealmRoles($id, ['editor', 'auditor']);
$users->removeRealmRoles($id, 'auditor');

$users->clientRoles($id, 'billing');
$users->assignClientRoles($id, 'billing', ['invoice-viewer']);
$users->removeClientRoles($id, 'billing', ['invoice-viewer']);
```

## Realm roles

```php
$roles = Keycloak::roles();

$roles->all(['search' => 'admin']);
$roles->names();
$roles->find('editor');
$roles->exists('editor');
$roles->create('editor', 'Can edit content', attributes: ['level' => '2']);
$roles->firstOrCreate('editor');
$roles->update('editor', ['description' => 'Editors']);
$roles->delete('editor');
$roles->users('editor');                  // users with this role
$roles->groups('editor');
$roles->addComposites('admin', ['editor', 'auditor']);
$roles->composites('admin');
```

## Groups

```php
$groups = Keycloak::groups();

$companyId = $groups->create('company', ['country' => 'EG']);
$engId     = $groups->createChild($companyId, 'engineering');

$groups->all(['search' => 'eng']);
$groups->search('engineering', exact: true);
$groups->find($engId);
$groups->findByPath('/company/engineering');
$groups->children($companyId);
$groups->count();
$groups->update($engId, ['attributes' => ['cost_center' => ['42']]]);
$groups->delete($engId);

$groups->members($engId, first: 0, max: 100);
$groups->cursorMembers($engId)->each(/* ... */);
$groups->addUser($engId, $userId);
$groups->removeUser($engId, $userId);

$groups->assignRealmRoles($engId, ['developer']);
$groups->removeRealmRoles($engId, ['developer']);
$groups->assignClientRoles($engId, 'billing', ['invoice-viewer']);
$groups->realmRoles($engId, effective: true);
```

## Clients

```php
$clients = Keycloak::clients();

$clients->all();
$clients->findByClientId('billing');
$clients->uuid('billing');                 // cached
$clients->find('billing');
$clients->create(['clientId' => 'reports', 'publicClient' => false, 'serviceAccountsEnabled' => true]);
$clients->update('reports', ['description' => 'Reporting service']);
$clients->delete('reports');

$clients->secret('billing');
$clients->regenerateSecret('billing');
$clients->serviceAccountUser('billing');
$clients->sessions('billing');

$clients->roles('billing');
$clients->role('billing', 'invoice-viewer');
$clients->createRole('billing', 'invoice-viewer', 'Read invoices');
$clients->deleteRole('billing', 'invoice-viewer');
$clients->roleUsers('billing', 'invoice-viewer');
```

## Realm

```php
$realm = Keycloak::admin()->realm();

$realm->get();                                    // realm representation
$realm->events(['type' => 'LOGIN_ERROR', 'max' => 50]);
$realm->adminEvents(['operationTypes' => 'DELETE']);
$realm->clientSessionStats();
$realm->logoutAll();
```

## Anything else

Call any Admin API endpoint directly. Paths are relative to `/admin/realms/{realm}`:

```php
$admin = Keycloak::admin();

$admin->get('identity-provider/instances');
$admin->post('client-scopes', ['name' => 'reports', 'protocol' => 'openid-connect']);
$admin->put("users/{$id}/groups/{$groupId}");
$admin->delete("client-scopes/{$scopeId}");

$response = $admin->send('GET', 'users', ['max' => 1], throw: false);   // Illuminate\Http\Client\Response
$admin->token();                                                        // the cached admin token
```

## Keeping the local users table in sync

The 1.x `KeycloakUsersService` is still available. It calls the Admin API **and** updates the local user row
in one step:

```php
use Bhry98\KeycloakAuth\Services\KeycloakUsersService;

$user = KeycloakUsersService::guard('web')->create([...]);   // returns the KCUserModel
KeycloakUsersService::guard('web')->createOrUpdate(['email' => 'jane@example.com', /* ... */]);
KeycloakUsersService::guard('web')->setStatus($keycloakId, false);
```

## Example: invite a user

```php
public function invite(InviteRequest $request)
{
    $users = Keycloak::users();

    $id = $users->create([
        'username' => $request->email,
        'email' => $request->email,
        'first_name' => $request->first_name,
        'last_name' => $request->last_name,
        'required_actions' => ['VERIFY_EMAIL', 'UPDATE_PASSWORD'],
    ]);

    $users->assignRealmRoles($id, [$request->role]);
    $users->executeActionsEmail($id, ['VERIFY_EMAIL', 'UPDATE_PASSWORD'], lifespan: 86400, redirectUri: url('/'));

    return response()->json(['id' => $id], 201);
}
```
