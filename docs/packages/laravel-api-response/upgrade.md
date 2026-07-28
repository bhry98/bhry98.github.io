# Upgrade Guide

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

## New in this release

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
