-- TrustLens AI Supabase Schema v1.1
-- Complies with TrustLens_PRD_v1.1 Section 9.3 and Section 10 Security

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  plan text NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'team', 'enterprise')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 2. Daily Usage Table (Counts only - NO raw claims or visited URLs stored for privacy)
CREATE TABLE IF NOT EXISTS public.usage_daily (
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  day date NOT NULL DEFAULT CURRENT_DATE,
  claim_checks integer NOT NULL DEFAULT 0,
  url_scans integer NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);

-- 3. Enable Row-Level Security (MANDATORY: Section 10)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_daily ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for Profiles
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
CREATE POLICY "Users can read own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own display_name" ON public.profiles;
CREATE POLICY "Users can update own display_name"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (
    auth.uid() = id
  );

-- 5. RLS Policies for Daily Usage
DROP POLICY IF EXISTS "Users can read own daily usage" ON public.usage_daily;
CREATE POLICY "Users can read own daily usage"
  ON public.usage_daily
  FOR SELECT
  USING (auth.uid() = user_id);

-- Note: No INSERT or UPDATE policies are created for anon/authenticated roles on usage_daily.
-- Only the backend FastAPI service role (bypassing RLS) can write and increment usage counts.

-- 6. Trigger to auto-create profile on new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, plan)
  VALUES (
    new.id,
    COALESCE(
      new.raw_user_meta_data->>'full_name',
      new.raw_user_meta_data->>'display_name',
      new.raw_user_meta_data->>'name',
      split_part(new.email, '@', 1)
    ),
    'free'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 7. Helper RPC to increment usage atomically (called by backend service role)
CREATE OR REPLACE FUNCTION public.increment_usage(
  target_user_id uuid,
  usage_type text, -- 'claim' or 'url'
  usage_day date DEFAULT CURRENT_DATE
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_claim_checks int;
  current_url_scans int;
BEGIN
  INSERT INTO public.usage_daily (user_id, day, claim_checks, url_scans)
  VALUES (
    target_user_id,
    usage_day,
    CASE WHEN usage_type = 'claim' THEN 1 ELSE 0 END,
    CASE WHEN usage_type = 'url' THEN 1 ELSE 0 END
  )
  ON CONFLICT (user_id, day) DO UPDATE
  SET
    claim_checks = public.usage_daily.claim_checks + (CASE WHEN usage_type = 'claim' THEN 1 ELSE 0 END),
    url_scans = public.usage_daily.url_scans + (CASE WHEN usage_type = 'url' THEN 1 ELSE 0 END)
  RETURNING claim_checks, url_scans INTO current_claim_checks, current_url_scans;

  RETURN json_build_object(
    'user_id', target_user_id,
    'day', usage_day,
    'claim_checks', current_claim_checks,
    'url_scans', current_url_scans
  );
END;
$$;
