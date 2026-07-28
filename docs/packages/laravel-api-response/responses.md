# Responses

## Basic usage

The `api()` helper (and the `ApiResponse` facade) resolve a **fresh** fluent builder every time you call them - safe to chain, never shared state between responses.

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

`ResponseBuilder` implements Laravel's `Responsable` contract, so you can skip `->send()` entirely and return the builder directly from a controller or route closure:

```php
return api()->created($user);
```

Default JSON shape:

```json
{
  "status": true,
  "message": "User created.",
  "data": { "id": 1 }
}
```

## Ready-made responses

### HTTP shortcuts

```php
api()->ok($data);              // 200
api()->created($user);         // 201
api()->accepted();             // 202
api()->noContent();            // 204, empty body
api()->badRequest($msg, $errors); // 400
api()->unauthorized();         // 401
api()->forbidden();            // 403
api()->notFound();             // 404
api()->conflict();             // 409
api()->unprocessable($errors); // 422
api()->tooManyRequests();      // 429
api()->internal();             // 500
api()->serviceUnavailable();   // 503
```

### Business shortcuts

```php
api()->saved($model);
api()->updated($model);
api()->deleted();
api()->restored($model);
api()->archived($model);
api()->verified($user);
api()->registered($user);      // 201
api()->loggedIn($user);
api()->loggedOut();
api()->passwordChanged();
api()->uploaded($file);        // 201
api()->download($url);
api()->emailSent();
api()->otpSent();
```

Every shortcut accepts an optional message override (`api()->updated('Custom message.')`) and pulls its default from `config('bhry98-api-response.messages')` otherwise.

## Advanced usage

```php
return api()
    ->success()
    ->message('Order placed.')
    ->data($order)
    ->meta(['queue_position' => 4])
    ->links(['tracking' => route('orders.track', $order)])
    ->extra(['request_id' => (string) Str::uuid()])
    ->headers(['X-Order-Id' => $order->id])
    ->cookie(Cookie::create('last_order')->withValue($order->id))
    ->version('v2')
    ->send();
```

- `data()` / `from()` - attach a payload (auto-detected, see [below](#automatic-data-detection)).
- `meta()` / `links()` - merge into the `meta` / `links` blocks.
- `errors()` - merge into the `errors` block (used automatically by `badRequest()`/`unprocessable()`).
- `extra()` - merge extra keys into the **top level** of the envelope.
- `headers()` / `cookie()` / `cookies()` - attach to the final `JsonResponse`.
- `statusCode()` - set any arbitrary HTTP status.
- `preset()` - pick a response shape for this call only (see [Presets](customization.md#presets--configurable-json-structure)).
- `version()` - override `config('bhry98-api-response.version')` for this response.
- `localize($key)` - translate the current (or given) message through Laravel's translator.

## Templates

Define reusable, named responses in config:

```php
// config/bhry98-api-response.php
'responses' => [
    'user_created' => [
        'status' => true,
        'message' => 'User created successfully.',
        'code' => 201,
    ],
    'invoice_paid' => [
        'status' => true,
        'message' => 'Invoice paid.',
        'code' => 200,
    ],
],
```

```php
return api()->template('user_created');

// override individual fields per call
return api()->template('user_created', ['data' => $user]);
```

## Macros

Register your own reusable responses - `ResponseBuilder` (and therefore `api()`/`ApiResponse`) is fully `Macroable`:

```php
use Bhry98\LaravelApiResponse\Facades\ApiResponse;

ApiResponse::macro('invoicePaid', function (Invoice $invoice) {
    /** @var \Bhry98\LaravelApiResponse\Builder\ResponseBuilder $this */
    return $this->success()->message('Invoice paid.')->data($invoice);
});

return api()->invoicePaid($invoice);
```

## Automatic data detection

`data()` (and its aliases `from()`, `resource()`, `resourceCollection()`, `paginate()`) automatically normalize whatever you pass in:

```php
return api()->from($user);              // Eloquent model
return api()->from($users);              // Collection
return api()->from(UserResource::make($user));         // JsonResource
return api()->from(UserResource::collection($users));  // ResourceCollection
return api()->from($paginator);          // LengthAwarePaginator / CursorPaginator
return api()->from($invoiceDto);         // any Arrayable DTO
return api()->from(['id' => 1]);         // plain array - passed through untouched
```

Pagination and resource-collection meta/links are lifted into the envelope's top-level `meta`/`links` automatically.

## Pagination

```php
return api()->paginate($users);
```

```json
{
  "status": true,
  "message": "Operation successful.",
  "data": [ ... ],
  "meta": { "current_page": 1, "last_page": 5, "per_page": 15, "total": 72, "from": 1, "to": 15 },
  "links": { "first": "...", "last": "...", "prev": null, "next": "..." }
}
```

Works identically for `CursorPaginator` and for a `ResourceCollection` built on top of either paginator.

## Resources

```php
api()->resource(UserResource::make($user));
api()->resourceCollection(UserResource::collection($users));
```

## Next

[Customization](customization.md) covers the envelope shape, global metadata, rate limiting, audit logging, locale resolution, hooks/events and exception handling.
