# Upgrade Guide

## Upgrading to 2.1

```bash
composer require bhry98/laravel-api-response:^2.1
```

There are no breaking API changes. This release adds support for newer Laravel and PHP versions and fixes several bugs.

### Supported versions

- **Laravel 14** is allowed (`^11.0|^12.0|^13.0|^14.0`) and tested against its development branch.
- **PHP 8.5** is tested on every supported Laravel version.
- The package now requires `laravel/framework` directly instead of a partial list of `illuminate/*` components. It always relied on parts of the framework that aren't published separately (such as `Illuminate\Foundation`), so this only makes the real requirement explicit. Laravel apps aren't affected.

### Bug fixes

- **No more double-wrapped responses.** With `override_default_response` enabled, `api()` responses (and the legacy `BResponse*` ones) used to be wrapped a second time: `{"status": true, "data": {"status": true, "message": ...}}`. They are now always sent exactly once.
- **`exceptions.map` is now applied.** The map in the config used to be ignored. You can now remap built-in exceptions and register your own exception classes with a status code. See [Exception handling](customization.md#exception-handling).
- **`ModelNotFoundException` no longer leaks internals.** Laravel converts it to a `NotFoundHttpException` before render callbacks run, so the response used to say `No query results for model [App\Models\User] 5`. It now returns the generic "Resource not found." message.
- **`AuthorizationException` keeps its status.** `Gate::denyWithStatus()` / `denyAsNotFound()` statuses are respected.
- **HTTP exception headers are kept.** `Retry-After`, `Allow` and other headers on an `HttpException` now reach the client.
- **Audit log: `Authorization` headers are redacted.** With `capture.headers` on, header values (which are arrays) were never redacted, so bearer tokens ended up in the log. Hidden keys are now redacted at every level.
- **Audit log: file uploads work with the queue.** Requests that contained an uploaded file made the queued job fail, because uploaded files can't be serialized. They are now stored as a `{file, size, mime}` description.
- **Audit log: smaller fixes.** `methods` is case-insensitive, and user agents longer than 255 characters are truncated instead of breaking the insert on MySQL.
- **Debug info from `->trace()` is kept** when the global `debug` block is enabled. The global block used to overwrite it.
- **`localize()`** ignores a key that resolves to a whole translation group (an array) instead of throwing a `TypeError`.
- **Locale resolution** ignores `Accept-Language` tags with `q=0`, which means "not acceptable".
- **Testing macros** (`assertApiSuccess()`, `assertApiValidation()`, ...) now work when `wrap` is enabled.
- **Exception rendering** is now registered even if the exception handler was resolved before the package's service provider booted.
- The rate-limit docs example was wrong: `api.rate_limit:5,1` means 5 attempts per **second**. Use `api.rate_limit:5,60` for 5 per minute.

### Optional: audit log `user_id` column

New installs create `user_id` as a `string(64)` column, so UUID and ULID user keys fit. If you already ran the old migration and your users have non-integer keys, change the column yourself:

```php
Schema::table('api_response_audit_logs', function (Blueprint $table) {
    $table->string('user_id', 64)->nullable()->change();
});
```

Integer user keys keep working with the old column, so you don't need to do anything for them.


## Backward compatibility & migration

The pre-2.0 API (`BResponseSuccess`, `BResponseError`, `BResponseValidationError`, `BResponseNotFound`, `BResponseInternalError` and the underlying `Helpers\BaseResponse`) still works unchanged and is not going away - it is marked `@deprecated` in favor of `api()`/`ApiResponse`, nothing more.

One behavioral fix ships alongside: previously `toJson()` duplicated (and diverged from) `toArray()`'s logic, ignoring `config('keys')`/`config('wrap')` entirely and emitting the raw HTTP status code as the `status` value. `toJson()` now simply delegates to `toArray()`, so both honor your configured keys/wrap, and `status` is a boolean (`< 400`) as documented - matching the shape every new response produced by `api()` already used.

```php
// still works exactly as before
use Bhry98\LaravelApiResponse\Facades\BResponseSuccess;

return BResponseSuccess::make()
    ->message('Everything is fine!')
    ->data(['id' => 1])
    ->additions(['request_id' => uniqid()])
    ->toJson();
```

## New in 2.0

Three cross-cutting concerns joined the package as opt-in middleware, each config-driven with sensible defaults - nothing below changes behavior until you turn it on:

- **Rate limiting** (`api.rate_limit`) - see [Customization → Rate limiting](customization.md#rate-limiting).
- **Audit logging** (`api.audit`) - see [Customization → Audit logging](customization.md#audit-logging). Requires publishing and running the new migration if you enable it.
- **Locale resolution** (`api.locale`) - see [Customization → Localization](customization.md#localization).

If you're upgrading from a version before these existed, re-publish the config to pick up the new `rate_limit`, `audit_log` and `locale` sections:

```bash
php artisan vendor:publish --tag=bhry98-api-response-config --force
```

(Back up any custom edits to `config/bhry98-api-response.php` first - `--force` overwrites the whole file.)

## Architecture

```
src/
  Builder/        ResponseBuilder + its Concerns traits (fluent state, HTTP/business shortcuts, templates, terminal methods)
  Contracts/      Interfaces: ResponseBuilderContract, ResponseFormatterContract, PresetContract, DataResolverContract, MetaProviderContract, PipelineStageContract
  Data/           ResponsePayload (the mutable value object threaded through the pipeline)
  Enums/          MetaKey, Preset
  Events/         ResponseCreated, ResponseFailed, ResponseSent
  Exceptions/     TemplateNotFoundException, PresetNotFoundException, ExceptionRenderer
  Facades/        ApiResponse (+ deprecated legacy facades)
  Formatters/     DefaultFormatter, MinimalFormatter, MobileFormatter, JsonApiFormatter
  Helpers/        Legacy BaseResponse / ResponseKeys (deprecated, BC only)
  Hooks/          HookRegistry (before/after)
  Jobs/           StoreAuditLogEntry (queued audit log writer)
  Middleware/     AttachRequestId, ApiRateLimit, AuditRequests, ResolveLocale (all optional)
  Models/         AuditLog
  Pipeline/       ResponsePipeline + Stages (data resolution, global meta, debug, hooks, events)
  Presets/        PresetManager + built-in presets
  Providers/      BResponseServiceProvider
  Responses/      Legacy per-type response classes (deprecated, BC only)
  Support/        DataResolver, MetaProviderRegistry, DebugCollector, meta providers, response-factory override
  Testing/        TestResponse assertion macros
database/
  migrations/     Publishable audit_log table migration
```

Every piece is bound through the container and swappable - nothing is a static god-class, and `ResponseBuilder` itself is always resolved fresh (never a singleton) so fluent state is never shared between responses.
