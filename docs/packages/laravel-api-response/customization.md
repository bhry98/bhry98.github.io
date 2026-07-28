# Customization

## Presets & configurable JSON structure

Every top-level key is renameable:

```php
'keys' => [
    'status' => 'success',
    'message' => 'msg',
    'data' => 'result',
],
```

```json
{ "success": true, "msg": "...", "result": {} }
```

Set `'wrap' => true` to nest the whole envelope under a top-level `data` key.

Four built-in **presets** control the overall response *shape* (not just key names):

| Preset | Behaviour |
|---|---|
| `default` | The standard `{status, message, data, errors?, meta?, links?}` envelope. |
| `minimal` | Only `{status, message, data, errors?}` - no meta/links/extras/debug. |
| `mobile` | Same as `default` but recursively strips `null` values to save bandwidth. |
| `jsonapi` | A JSON:API-inspired `{data, meta, links, errors}` shape (not a strict spec implementation). |

```php
config(['bhry98-api-response.preset' => 'minimal']); // global default

return api()->preset('jsonapi')->success()->data($user); // per response
```

Register your own preset:

```php
use Bhry98\LaravelApiResponse\Contracts\{PresetContract, ResponseFormatterContract};
use Bhry98\LaravelApiResponse\Presets\PresetManager;

class ShoutyFormatter implements ResponseFormatterContract
{
    public function format(\Bhry98\LaravelApiResponse\Data\ResponsePayload $payload): array
    {
        return ['STATUS' => $payload->success, 'MESSAGE' => strtoupper($payload->message)];
    }
}

class ShoutyPreset implements PresetContract
{
    public function __construct(private ShoutyFormatter $formatter) {}
    public function formatter(): ResponseFormatterContract { return $this->formatter; }
}

// in a service provider
app(PresetManager::class)->register('shouty', ShoutyPreset::class);

return api()->preset('shouty')->success()->message('done');
```

## Global metadata

Opt in per key:

```php
'meta' => [
    'enabled' => ['request_id', 'execution_time', 'api_version', 'locale'],
],
```

```json
{ "meta": { "request_id": "...", "execution_time": "12.4ms", "api_version": "v1", "locale": "en" } }
```

Explicit `->meta([...])` values always win over the automatic ones on key collisions. Add your own provider by implementing `MetaProviderContract` and registering it under `meta.providers`.

There is also an optional `AttachRequestId` middleware that reuses an incoming `X-Request-Id` header (or generates one) and echoes it back as a response header, so the `request_id` meta stays consistent with your logs:

```php
// bootstrap/app.php
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(\Bhry98\LaravelApiResponse\Middleware\AttachRequestId::class);
})
```

## Debug mode

Development only - requires **both** flags to be true, so it can never leak into production by accident:

```php
'debug' => [
    'enabled' => env('API_RESPONSE_DEBUG', false),
    'include' => ['queries', 'time', 'memory', 'exception', 'trace'],
],
```

```json
{ "debug": { "execution_time_ms": 12.4, "memory_usage_mb": 8.1, "queries": [...] } }
```

## API versioning

```php
'version' => env('API_RESPONSE_VERSION', 'v1'),
```

```php
return api()->version('v2')->success(); // overrides for this response
```

Exposed automatically via the `api_version` meta provider when enabled.

## Localization

### Translating messages

```php
return api()->updated()->localize('bhry98-api-response::api.updated');
```

The package ships `lang/en/api.php` (publishable to `lang/vendor/bhry98-api-response`) with an entry per ready-made shortcut. `config('bhry98-api-response.messages')` remains the primary/default source so a config override is never silently shadowed by a translation - use `localize()` explicitly when you want locale-driven messages instead.

### Resolving the request's locale (Accept-Language + user column)

Opt-in per-request locale resolution via the `api.locale` middleware alias. It resolves a locale in this priority order and calls `App::setLocale()`:

1. The **`Accept-Language`** request header (first tag, e.g. `fr` out of `fr-CA;q=0.9,en;q=0.5`), matched against `locale.supported` when that list is non-empty.
2. The **authenticated user's locale column** - the column name is configurable, so this works whatever your `users` table calls it (`locale`, `lang`, `preferred_language`, ...).
3. `locale.fallback` (defaults to `config('app.locale')`).

```php
'locale' => [
    'enabled' => env('API_RESPONSE_LOCALE_ENABLED', false),
    'supported' => ['en', 'ar', 'fr'], // empty array = accept any tag from the header
    'user_column' => env('API_RESPONSE_LOCALE_USER_COLUMN', 'locale'),
    'fallback' => env('API_RESPONSE_LOCALE_FALLBACK', config('app.locale', 'en')),
],
```

```php
// bootstrap/app.php
->withMiddleware(function (Middleware $middleware) {
    $middleware->appendToGroup('api', 'api.locale');
})
```

Combine with the `locale` global metadata provider (above) to echo the resolved locale back on every response.

## Rate limiting

Opt-in throttling for any route/group via the `api.rate_limit` middleware alias. It wraps Laravel's own `RateLimiter`, but returns a standard `api()->tooManyRequests()` envelope - with `Retry-After`/`X-RateLimit-*` headers - instead of the framework's default `ThrottleRequestsException` response.

```php
'rate_limit' => [
    'enabled' => env('API_RESPONSE_RATE_LIMIT_ENABLED', false),
    'max_attempts' => env('API_RESPONSE_RATE_LIMIT_MAX_ATTEMPTS', 60),
    'decay_seconds' => env('API_RESPONSE_RATE_LIMIT_DECAY_SECONDS', 60),
    'by' => env('API_RESPONSE_RATE_LIMIT_BY', 'ip'), // "ip", "user" or "route"
    'key_prefix' => env('API_RESPONSE_RATE_LIMIT_PREFIX', 'api-response-rate-limit'),
    'message' => null, // null falls back to messages.too_many_requests
],
```

```php
// bootstrap/app.php
->withMiddleware(function (Middleware $middleware) {
    $middleware->appendToGroup('api', 'api.rate_limit');
})
```

Override the configured `max_attempts`/`decay_seconds` for a specific route via middleware parameters:

```php
Route::post('/login', ...)->middleware('api.rate_limit:5,1'); // 5 attempts per minute
```

`by: 'user'` buckets authenticated requests by the user's auth identifier and falls back to IP for guests; `by: 'route'` buckets by route name (or URI path when unnamed).

## Audit logging

Opt-in request/response auditing via the `api.audit` middleware alias. Every matching request is written to the `api_response_audit_logs` table (name configurable) through the queued `StoreAuditLogEntry` job **by default**, so logging never adds latency to the actual response - set `queue.enabled` to `false` to write synchronously instead (handy for local dev/testing).

```php
'audit_log' => [
    'enabled' => env('API_RESPONSE_AUDIT_LOG_ENABLED', false),

    'connection' => env('API_RESPONSE_AUDIT_LOG_DB_CONNECTION'), // null = default DB connection
    'table' => env('API_RESPONSE_AUDIT_LOG_TABLE', 'api_response_audit_logs'),

    'queue' => [
        'enabled' => env('API_RESPONSE_AUDIT_LOG_QUEUE_ENABLED', true),
        'connection' => env('API_RESPONSE_AUDIT_LOG_QUEUE_CONNECTION'), // null = config('queue.default')
        'queue' => env('API_RESPONSE_AUDIT_LOG_QUEUE_NAME'), // null = the connection's default queue
    ],

    'capture' => [
        'request_body' => true,
        'response_body' => true,
        'headers' => false,
    ],

    'methods' => [], // e.g. ['POST', 'PUT', 'PATCH', 'DELETE'] - empty means every method
    'exclude_routes' => [], // route names or URI patterns (fnmatch), e.g. 'telescope*'

    'hidden' => [
        'password', 'password_confirmation', 'token', 'secret',
        'authorization', 'api_key', 'access_token', 'refresh_token', 'card_number', 'cvv',
    ],
],
```

```bash
php artisan vendor:publish --tag=bhry98-api-response-migrations
php artisan migrate
```

```php
// bootstrap/app.php
->withMiddleware(function (Middleware $middleware) {
    $middleware->appendToGroup('api', 'api.audit');
})
```

- `queue.connection`/`queue.queue` map directly onto `StoreAuditLogEntry::onConnection()`/`onQueue()`. Leave them `null` to use your app's default queue connection (`config('queue.default')`, e.g. `sync`, `database`, `redis`, ...) - set `queue.connection` to `'database'` (or `'redis'`, etc.) explicitly if you want audit logs on a *different* connection than the rest of your app's jobs.
- Anything listed under `hidden` is redacted (replaced with `"***"`) wherever it appears as a request/response body (or header, if `capture.headers` is on) key, at any nesting depth, before the entry is persisted.
- Query the log like any other Eloquent model:

```php
use Bhry98\LaravelApiResponse\Models\AuditLog;

AuditLog::where('user_id', $user->id)->latest('created_at')->get();
```

## Hooks

Run arbitrary logic against every response before it is formatted:

```php
use Bhry98\LaravelApiResponse\Facades\ApiResponse;
use Bhry98\LaravelApiResponse\Data\ResponsePayload;

ApiResponse::before(function (ResponsePayload $payload) {
    $payload->extra['server'] = gethostname();
});

ApiResponse::after(function (ResponsePayload $payload) {
    Log::info('api.response', ['status' => $payload->success]);
});
```

## Events

```php
Bhry98\LaravelApiResponse\Events\ResponseCreated::class; // fired for every response
Bhry98\LaravelApiResponse\Events\ResponseFailed::class;  // fired when success === false
Bhry98\LaravelApiResponse\Events\ResponseSent::class;    // fired once the JsonResponse is built
```

## Exception handling

Fully opt-in - off by default:

```php
'exceptions' => [
    'override_exception_handler' => env('API_RESPONSE_OVERRIDE_EXCEPTIONS', false),
],
```

When enabled, `ValidationException`, `AuthenticationException`, `AuthorizationException`, `ModelNotFoundException` and any `HttpExceptionInterface` are automatically formatted as `api()` responses for JSON/`api/*` requests; anything else becomes `api()->internal()` (with the real message only when `app.debug` is true).

## Overriding the default `response()->json()`

Also fully opt-in:

```php
'override_default_response' => env('API_RESPONSE_OVERRIDE_DEFAULT', false),
```

```php
// with the flag enabled
return response()->json(['id' => 1]);
// => {"status": true, "data": {"id": 1}}
```

Never forced - leave it `false` (the default) and `response()->json()` behaves exactly like stock Laravel.

## Testing helpers

Registered automatically on `Illuminate\Testing\TestResponse` - no trait/import needed:

```php
$response->assertApiSuccess('User created.');
$response->assertApiError('Something went wrong.');
$response->assertApiValidation(['email']);
$response->assertApiMessage('User created.');
$response->assertApiStatus(true);
$response->assertApiData(['id' => 1]);
```

## Extending the package

- **Formatters** - implement `ResponseFormatterContract` for a fully custom envelope shape.
- **Presets** - implement `PresetContract` and register via `PresetManager::register()`.
- **Data resolvers** - the default `DataResolverContract` binding (`DataResolver`) can be swapped in your own service provider if you need custom auto-detection.
- **Meta providers** - implement `MetaProviderContract`, register under `meta.providers`, then list the key under `meta.enabled`.
- **Macros** - `ResponseBuilder::macro()` / `ApiResponse::macro()` for one-off custom shortcuts.
- **Hooks** - `ApiResponse::before()` / `ApiResponse::after()` for cross-cutting concerns (logging, request ids, ...).
- **Events** - listen to `ResponseCreated` / `ResponseFailed` / `ResponseSent`.

## Next

See the [Upgrade Guide](upgrade.md) for backward compatibility with the pre-2.0 API and a look at the package's internal architecture.
