-- TrustLens Supabase migration 001
-- All application-owned objects live in the trustlens schema.
-- Run only against the TrustLens database.

BEGIN;

CREATE SCHEMA IF NOT EXISTS trustlens;

CREATE TABLE IF NOT EXISTS trustlens.migration_history (
  version text PRIMARY KEY,
  name text NOT NULL,
  checksum text NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trustlens.migration_locks (
  lock_name text PRIMARY KEY,
  owner text NOT NULL,
  acquired_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trustlens.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  plan text NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'team', 'enterprise')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trustlens.usage_daily (
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  day date NOT NULL DEFAULT CURRENT_DATE,
  claim_checks integer NOT NULL DEFAULT 0 CHECK (claim_checks >= 0),
  url_scans integer NOT NULL DEFAULT 0 CHECK (url_scans >= 0),
  PRIMARY KEY (user_id, day)
);

ALTER TABLE trustlens.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trustlens.usage_daily ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own profile" ON trustlens.profiles;
CREATE POLICY "Users can read own profile" ON trustlens.profiles
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own display_name" ON trustlens.profiles;
CREATE POLICY "Users can update own display_name" ON trustlens.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can read own daily usage" ON trustlens.usage_daily;
CREATE POLICY "Users can read own daily usage" ON trustlens.usage_daily
  FOR SELECT USING (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION trustlens.handle_new_user()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = trustlens, auth
AS $$
BEGIN
  INSERT INTO trustlens.profiles (id, display_name, plan)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'display_name', new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    'free'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION trustlens.handle_new_user();

CREATE OR REPLACE FUNCTION trustlens.increment_usage(
  target_user_id uuid,
  usage_type text,
  usage_day date DEFAULT CURRENT_DATE
)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER SET search_path = trustlens
AS $$
DECLARE result_usage trustlens.usage_daily;
BEGIN
  IF usage_type NOT IN ('claim', 'url') THEN
    RAISE EXCEPTION 'Invalid usage type: %', usage_type;
  END IF;

  INSERT INTO trustlens.usage_daily (user_id, day, claim_checks, url_scans)
  VALUES (target_user_id, usage_day,
    CASE WHEN usage_type = 'claim' THEN 1 ELSE 0 END,
    CASE WHEN usage_type = 'url' THEN 1 ELSE 0 END)
  ON CONFLICT (user_id, day) DO UPDATE
  SET
    claim_checks = trustlens.usage_daily.claim_checks + CASE WHEN usage_type = 'claim' THEN 1 ELSE 0 END,
    url_scans = trustlens.usage_daily.url_scans + CASE WHEN usage_type = 'url' THEN 1 ELSE 0 END
  RETURNING * INTO result_usage;

  RETURN json_build_object(
    'user_id', result_usage.user_id,
    'day', result_usage.day,
    'claim_checks', result_usage.claim_checks,
    'url_scans', result_usage.url_scans
  );
END;
$$;

-- Fail the migration if required application objects are absent.
DO $$
DECLARE missing integer;
BEGIN
  SELECT count(*) INTO missing
  FROM (VALUES ('profiles'), ('usage_daily')) AS required(name)
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='trustlens' AND c.relname=required.name AND c.relkind='r'
  );
  IF missing > 0 THEN
    RAISE EXCEPTION 'TrustLens migration postcondition failed: % tables missing', missing;
  END IF;
END;
$$;

COMMIT;
