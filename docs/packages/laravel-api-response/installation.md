# Installation

## Requirements

| | |
|---|---|
| PHP | 8.2 or newer (8.2 – 8.5 tested) |
| Laravel | 11.x, 12.x, 13.x or 14.x |

See the [compatibility table](index.md#compatibility) for the exact PHP versions each Laravel release supports.

## Install via Composer

```bash
composer require bhry98/laravel-api-response
```

The service provider and the `ApiResponse` facade alias are auto-discovered - nothing else is required. Every feature documented here works out of the box with sensible defaults; rate limiting, audit logging and locale resolution are all opt-in.

## Publishing

### Config

```bash
php artisan vendor:publish --tag=bhry98-api-response-config
```

Creates `config/bhry98-api-response.php` with commented sections for keys, wrapping, messages, templates, meta, versioning, debug mode, exception handling, the response-factory override, **rate limiting**, **audit logging** and **locale resolution**. Every feature in these docs maps to a section in that file.

### Translations

```bash
php artisan vendor:publish --tag=bhry98-api-response-lang
```

Publishes `lang/vendor/bhry98-api-response` - see [Localization](customization.md#localization).

### Audit log migration

Only needed if you turn on [audit logging](customization.md#audit-logging):

```bash
php artisan vendor:publish --tag=bhry98-api-response-migrations
php artisan migrate
```

This publishes a timestamped migration that creates the `api_response_audit_logs` table. The table name is configurable via `audit_log.table`, and the database connection via `audit_log.connection`.

## Next

Head to [Responses](responses.md) to start sending your first `api()` response, or to [Customization](customization.md) to wire up rate limiting, audit logging or locale resolution.
