'use server';

import { redirect } from 'next/navigation';
import { headers } from 'next/headers';
import { createClient } from '@/lib/supabase/server';
import { createAdminClient } from '@/lib/supabase/admin';
import { getSafeRedirectUrl } from '@/lib/auth-utils';

export type AuthState = {
  error?: string;
  success?: string;
  message?: string;
};

export async function loginAction(prevState: AuthState | null, formData: FormData): Promise<AuthState> {
  const email = (formData.get('email') as string)?.trim();
  const password = formData.get('password') as string;
  const next = formData.get('next') as string;

  if (!email || !password) {
    return { error: 'Please provide both your email and password.' };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    // FR-A6: Login errors must say what to do and NEVER reveal whether an email exists
    return {
      error: 'Invalid email or password. Please check your credentials and try again.',
    };
  }

  const safeTarget = getSafeRedirectUrl(next, '/dashboard');
  redirect(safeTarget);
}

export async function signupAction(prevState: AuthState | null, formData: FormData): Promise<AuthState> {
  const email = (formData.get('email') as string)?.trim();
  const password = formData.get('password') as string;
  const displayName = ((formData.get('displayName') as string) || '').trim();
  const next = formData.get('next') as string;

  if (!email || !password) {
    return { error: 'Email and password are required.' };
  }

  // FR-A1: Password minimum 8 characters
  if (password.length < 8) {
    return { error: 'Password must be at least 8 characters long.' };
  }

  const headerList = await headers();
  const origin = headerList.get('origin') || 'http://localhost:3000';
  const callbackUrl = `${origin}/auth/callback?next=${encodeURIComponent(getSafeRedirectUrl(next, '/dashboard'))}`;

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        display_name: displayName || email.split('@')[0],
        full_name: displayName || email.split('@')[0],
      },
      emailRedirectTo: callbackUrl,
    },
  });

  if (error) {
    return { error: error.message || 'Unable to complete sign up. Please try again.' };
  }

  // If Supabase requires email verification
  if (data.user && !data.session) {
    return {
      success: 'Account created! Please check your email inbox to confirm your account and sign in.',
    };
  }

  const safeTarget = getSafeRedirectUrl(next, '/dashboard');
  redirect(safeTarget);
}

export async function signoutAction() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect('/login');
}

export async function deleteAccountAction(): Promise<AuthState> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: 'Not authenticated' };
  }

  try {
    const admin = createAdminClient();
    // Delete profile and usage rows (they cascade from auth.users, or delete explicitly)
    await admin.from('usage_daily').delete().eq('user_id', user.id);
    await admin.from('profiles').delete().eq('id', user.id);
    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) {
      throw error;
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Unknown error';
    return { error: `Failed to delete account: ${msg}` };
  }

  await supabase.auth.signOut();
  redirect('/login?deleted=1');
}

export async function updateDisplayNameAction(displayName: string): Promise<AuthState> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: 'Not authenticated' };
  }

  const cleanName = displayName.trim();
  if (!cleanName) {
    return { error: 'Display name cannot be blank.' };
  }

  const { error } = await supabase
    .from('profiles')
    .update({ display_name: cleanName })
    .eq('id', user.id);

  if (error) {
    return { error: error.message };
  }

  return { success: 'Display name updated successfully.' };
}
