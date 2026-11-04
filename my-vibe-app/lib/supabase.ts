import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://uoqbgrstwynvsbtosbim.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

/**
 * Standard client-side Supabase instance.
 * Safe for public use in browser and client components (governed by Row Level Security).
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Client-side Supabase client accessor.
 */
export const getSupabaseClient = () => {
  const key = supabaseAnonKey || supabaseServiceRoleKey;
  if (!key) {
    throw new Error('No Supabase key configured. Please set NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local.');
  }
  return createClient(supabaseUrl, key);
};

/**
 * Server-side Supabase admin client.
 * Uses the Service Role Key with full administrative access (bypasses RLS).
 * MUST only be used in Server Components, Server Actions, or Route Handlers.
 */
export const getSupabaseAdmin = () => {
  if (!supabaseServiceRoleKey) {
    throw new Error('Missing SUPABASE_SERVICE_ROLE_KEY in environment variables.');
  }
  return createClient(supabaseUrl, supabaseServiceRoleKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });
};

export default supabase;
