---
date: 2026-10-28
slug: consistent-laravel-api-responses
authors:
  - bhry98
categories:
  - Laravel
  - Open Source
description: Why a single JSON response envelope makes frontend and mobile teams faster, and how to adopt one in Laravel.
---

# Consistent JSON responses in Laravel APIs

Every API that grows past a handful of endpoints ends up with the same problem: one controller
returns `{"data": ...}`, another returns `{"success": true, "result": ...}`, validation errors look
completely different from authorization errors, and the mobile team writes a separate parser for
each one.

A **single, predictable response envelope** fixes this, and it costs very little to adopt.

<!-- more -->

## What "consistent" actually means

Clients should be able to rely on the same shape for *every* response:

```json
{
  "status": true,
  "message": "User created.",
  "data": { "id": 1 }
}
```

and for every error:

```json
{
  "status": false,
  "message": "The given data was invalid.",
  "errors": { "email": ["The email field is required."] }
}
```

With that contract in place, a frontend can write **one** response handler: show `message`
in a toast, bind `data` to the view, map `errors` to form fields. No special cases.

## The usual approach — and where it breaks

Most teams start with a base controller or a trait:

```php
protected function success($data, string $message = '', int $code = 200)
{
    return response()->json([
        'status' => true,
        'message' => $message,
        'data' => $data,
    ], $code);
}
```

It works, until you need pagination metadata, API resources, a different shape for mobile,
consistent exception handling, rate-limit responses, or tests that assert on the envelope. Each
of those gets bolted on separately — and drifts.

## A fluent builder instead

That's why I built [**Laravel API Response**](../../packages/laravel-api-response/index.md). It
gives you one fluent builder for every response:

```php
// 201 with the standard envelope
return api()->created($user);

// fully customised
return api()
    ->success()
    ->message('Order placed.')
    ->data($order)
    ->meta(['queue_position' => 4])
    ->headers(['X-Order-Id' => $order->id])
    ->send();
```

The builder implements Laravel's `Responsable` contract, so you can return it directly from a
controller. Models, collections, `JsonResource`s and paginators are detected and normalised
automatically.

### Ready-made shortcuts

HTTP and business-level shortcuts keep controllers short and messages consistent:

```php
api()->notFound();
api()->unprocessable($errors);
api()->updated($model);
api()->loggedOut();
```

### One shape for exceptions too

Turn on the opt-in exception handling and validation, authentication, authorization and
"model not found" exceptions are rendered in the same envelope for JSON requests:

```php
// config/bhry98-api-response.php
'exceptions' => [
    'override_exception_handler' => env('API_RESPONSE_OVERRIDE_EXCEPTIONS', false),
],
```

### Tests that read like the contract

```php
$this->postJson('/api/users', [])
    ->assertApiValidation(['email']);

$this->postJson('/api/users', $payload)
    ->assertApiSuccess('User created.');
```

## Adopting it in an existing API

1. `composer require bhry98/laravel-api-response`
2. Use `api()` in **new** endpoints first.
3. Rename envelope keys or pick a preset (`default`, `minimal`, `mobile`, `jsonapi`) so it matches
   what your clients already expect.
4. Migrate older controllers gradually — nothing forces a big-bang rewrite.

!!! tip
    Agree on the envelope with your frontend and mobile developers *before* you write the
    first endpoint. It's a five-minute conversation that saves weeks of glue code.

Full documentation: [Installation](../../packages/laravel-api-response/installation.md) ·
[Responses](../../packages/laravel-api-response/responses.md) ·
[Customization](../../packages/laravel-api-response/customization.md)
