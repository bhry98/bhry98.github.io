---
date: 2026-08-20
slug: laravel-minio-object-storage
authors:
  - bhry98
categories:
  - Infrastructure
  - Laravel
description: Self-hosted, S3-compatible file storage for Laravel with MinIO — setup, configuration and secure downloads.
---

# S3-compatible storage for Laravel with MinIO

Storing uploads on the application server's disk works until you add a second server, move to
containers, or need backups you can trust. **Object storage** fixes that, and with **MinIO** you can
run it on your own infrastructure — useful when data has to stay on-premises.

<!-- more -->

## Why object storage

- **Shared** — every app server and pod sees the same files.
- **Scalable** — no more resizing disks.
- **S3 API** — the same code works against MinIO, AWS S3 and other compatible providers.
- **Secure sharing** — time-limited signed URLs instead of public folders.

## 1. Run MinIO

For local development:

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=change-me-please \
  -v minio-data:/data \
  quay.io/minio/minio server /data --console-address ":9001"
```

The S3 API listens on port `9000`; the web console is on `9001`. In production, run MinIO in
distributed mode behind TLS, and never use the root credentials from your application.

## 2. Create a bucket and an application user

With the MinIO client (`mc`):

```bash
mc alias set local http://localhost:9000 minioadmin change-me-please
mc mb local/app-uploads
mc admin user add local laravel-app 'a-long-random-secret'
mc admin policy attach local readwrite --user laravel-app
```

!!! warning
    The built-in `readwrite` policy covers **all** buckets. For production, write a policy
    that only allows access to `app-uploads`.

## 3. Configure Laravel

Install the S3 driver for Flysystem:

```bash
composer require league/flysystem-aws-s3-v3 "^3.0" --with-all-dependencies
```

Point the `s3` disk at MinIO:

```ini
FILESYSTEM_DISK=s3
AWS_ACCESS_KEY_ID=laravel-app
AWS_SECRET_ACCESS_KEY=a-long-random-secret
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=app-uploads
AWS_ENDPOINT=http://localhost:9000
AWS_USE_PATH_STYLE_ENDPOINT=true
```

`AWS_USE_PATH_STYLE_ENDPOINT=true` matters: MinIO serves buckets as
`http://host:9000/bucket`, not as `bucket.host` subdomains.

## 4. Use it like any other disk

```php
use Illuminate\Support\Facades\Storage;

// upload
$path = $request->file('invoice')->store('invoices');

// read
$pdf = Storage::get($path);

// share securely for 10 minutes
$url = Storage::temporaryUrl($path, now()->addMinutes(10));
```

Keep the bucket **private** and hand out `temporaryUrl()` links. The signature expires, so a leaked
link stops working on its own.

## 5. Production checklist

- [x] TLS in front of MinIO (or terminate at your ingress)
- [x] Least-privilege policy per application
- [x] Versioning on buckets that hold important documents
- [x] Replication or regular backups to a second location
- [x] Lifecycle rules to expire temporary files

Want a self-hosted storage setup for your applications? [Get in touch](../../portfolio/contact.md).
