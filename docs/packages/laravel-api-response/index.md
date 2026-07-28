# Laravel API Response

A fluent, extensible, highly configurable API response toolkit for Laravel 11, 12 and 13. Zero configuration to get
started, endlessly customizable when you need it.

```

return api()->created($user);

return api()
    ->success()
    ->message('User created.')
    ->data($user)
    ->meta(['foo' => 'bar'])
    ->headers(['X-Foo' => 'bar'])
    ->send();

```

## Why this package

- **One fluent builder** (`api()` / `ApiResponse`) for every response your API sends - success, error, validation,
  pagination, resources.
- **Configurable envelope** - rename keys, wrap the payload, switch between `default`/`minimal`/`mobile`/`jsonapi`
  presets, or write your own formatter.
- **Automatic data detection** - pass an Eloquent model, a `Collection`, a `JsonResource`, a paginator, or a plain
  array/DTO; it's normalized the same way every time.
- **Cross-cutting concerns as opt-in middleware** - rate limiting, request/response audit logging, and
  Accept-Language-aware locale resolution, all driven by config.
- **Hooks, events, macros and presets** for every extension point, so nothing requires forking the package.
- **Fully backward compatible** with the pre-2.0 `BResponseSuccess`/`BResponseError`/... API.

## Where to go next

| Page                              | What's in it                                                                                                                                                                                      |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Installation](installation.md)   | Composer install, publishing config/lang/migrations, requirements.                                                                                                                                |
| [Responses](responses.md)         | Building and sending responses: basic usage, ready-made shortcuts, templates, macros, automatic data detection, pagination, resources.                                                            |
| [Customization](customization.md) | Presets & envelope shape, global metadata, debug mode, versioning, localization, **rate limiting**, **audit logging**, hooks, events, exception handling, testing helpers, extending the package. |
| [Upgrade Guide](upgrade.md)       | Backward compatibility with the pre-2.0 API and the package's internal architecture.                                                                                                              |

## Quick example

```php
use Bhry98\LaravelApiResponse\Facades\ApiResponse;

return api()
    ->success()
    ->message('User created.')
    ->data($user)
    ->send();

// identical, via the facade
return ApiResponse::success()->message('User created.')->data($user)->send();
```

Default JSON shape:

```json
{
    "status": true,
    "message": "User created.",
    "data": {
        "id": 1
    }
}
```
