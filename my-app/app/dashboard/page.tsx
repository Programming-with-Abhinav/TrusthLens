import { Suspense } from 'react';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import DashboardClient from './DashboardClient';

async function DashboardContent() {
  const supabase = await createClient();

  // FR-A4 & Section 10: Server-side validation using getUser()
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login?next=/dashboard');
  }

  // Fetch profile (RLS allows reading own row)
  const { data: profile } = await supabase
    .from('profiles')
    .select('display_name, plan, created_at')
    .eq('id', user.id)
    .maybeSingle();

  // Fetch today's usage (RLS allows reading own row)
  const today = new Date().toISOString().split('T')[0];
  const { data: usage } = await supabase
    .from('usage_daily')
    .select('claim_checks, url_scans, day')
    .eq('user_id', user.id)
    .eq('day', today)
    .maybeSingle();

  const userProfile = {
    display_name: profile?.display_name || user.email?.split('@')[0] || 'User',
    plan: profile?.plan || 'free',
    created_at: profile?.created_at || user.created_at || new Date().toISOString(),
  };

  const initialUsage = {
    claim_checks: usage?.claim_checks ?? 0,
    url_scans: usage?.url_scans ?? 0,
    day: usage?.day || today,
  };

  return (
    <DashboardClient
      user={{
        id: user.id,
        email: user.email || '',
      }}
      profile={userProfile}
      initialUsage={initialUsage}
    />
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
          <div className="flex items-center gap-3">
            <svg className="animate-spin h-5 w-5 text-cyan-400" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Loading TrustLens Dashboard...</span>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
