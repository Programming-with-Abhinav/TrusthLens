# TrustLens database migrations

Run migrations in numeric order against only the TrustLens database:

```powershell
psql "$env:DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/001_trustlens_core.sql
```

Do not run the legacy schema files as migrations. Application tables, migration history, and migration locks are owned by the `trustlens` PostgreSQL schema. Supabase PostgREST callers must send `Accept-Profile: trustlens` for reads and `Content-Profile: trustlens` for writes.
