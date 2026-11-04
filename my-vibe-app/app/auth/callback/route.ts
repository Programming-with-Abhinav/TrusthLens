import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { getSafeRedirectUrl } from '@/lib/auth-utils';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = getSafeRedirectUrl(searchParams.get('next'), '/dashboard');

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // If code exchange failed or no code provided, redirect to login with error
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
