'use client';

import React, { useState, useTransition, useEffect } from 'react';
import Link from 'next/link';
import {
  Shield,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Search,
  Globe,
  User,
  LogOut,
  Trash2,
  BarChart3,
  Key,
} from 'lucide-react';
import { signoutAction, deleteAccountAction, updateDisplayNameAction } from '@/app/auth/actions';
import { createClient } from '@/lib/supabase/client';

interface DashboardProps {
  user: {
    id: string;
    email: string;
  };
  profile: {
    display_name: string;
    plan: string;
    created_at: string;
  };
  initialUsage: {
    claim_checks: number;
    url_scans: number;
    day: string;
  };
}

interface ClaimSource {
  publisher: string;
  rating?: string;
  url?: string;
  verdict?: string;
}

interface ClaimItem {
  claim: string;
  verdict: string;
  sources?: ClaimSource[];
  synthesis?: string;
}

interface UrlScanResult {
  url: string;
  level: string;
  flags?: string[];
  threats?: string[];
  source?: string;
}

export default function DashboardClient({ user, profile, initialUsage }: DashboardProps) {
  const [displayName, setDisplayName] = useState(profile.display_name || '');
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameMessage, setNameMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const [usage, setUsage] = useState(initialUsage);
  const [sessionToken, setSessionToken] = useState<string>('');
  const [tokenCopied, setTokenCopied] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Verification Testing Widget State
  const [claimInput, setClaimInput] = useState('');
  const [claimLoading, setClaimLoading] = useState(false);
  const [claimResults, setClaimResults] = useState<ClaimItem[] | null>(null);
  const [claimError, setClaimError] = useState<string | null>(null);

  // URL Scan Widget State
  const [urlInput, setUrlInput] = useState('');
  const [urlLoading, setUrlLoading] = useState(false);
  const [urlResult, setUrlResult] = useState<UrlScanResult | null>(null);
  const [urlError, setUrlError] = useState<string | null>(null);

  // Fetch access token on client
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      if (data.session?.access_token) {
        setSessionToken(data.session.access_token);
      }
    });
  }, []);

  const handleCopyToken = () => {
    if (!sessionToken) return;
    navigator.clipboard.writeText(sessionToken);
    setTokenCopied(true);
    setTimeout(() => setTokenCopied(false), 2500);
  };

  const handleUpdateName = (e: React.FormEvent) => {
    e.preventDefault();
    setNameMessage(null);
    startTransition(async () => {
      const res = await updateDisplayNameAction(displayName);
      if (res.error) {
        setNameMessage(`Error: ${res.error}`);
      } else {
        setNameMessage('Name saved successfully.');
        setIsEditingName(false);
      }
    });
  };

  const handleDeleteAccount = () => {
    setDeleteError(null);
    startTransition(async () => {
      const res = await deleteAccountAction();
      if (res?.error) {
        setDeleteError(res.error);
      }
    });
  };

  const handleTestClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimInput.trim()) return;
    setClaimLoading(true);
    setClaimError(null);
    setClaimResults(null);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`;
      }

      // Calls local FastAPI backend at port 5500
      const res = await fetch('http://localhost:5500/api/verify', {
        method: 'POST',
        headers,
        body: JSON.stringify({ text: claimInput }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || `Request failed with status ${res.status}`);
      }

      const data = await res.json();
      setClaimResults(data.claims || []);
      // Update local counter
      setUsage((prev) => ({ ...prev, claim_checks: prev.claim_checks + (data.claims?.length || 1) }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setClaimError(msg || 'Failed to verify claim. Make sure FastAPI backend is running on http://localhost:5500');
    } finally {
      setClaimLoading(false);
    }
  };

  const handleTestUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setUrlLoading(true);
    setUrlError(null);
    setUrlResult(null);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`;
      }

      const res = await fetch('http://localhost:5500/api/scan', {
        method: 'POST',
        headers,
        body: JSON.stringify({ url: urlInput }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || `Request failed with status ${res.status}`);
      }

      const data = await res.json();
      setUrlResult(data);
      // Update local counter
      setUsage((prev) => ({ ...prev, url_scans: prev.url_scans + 1 }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setUrlError(msg || 'Failed to scan URL. Make sure FastAPI backend is running on http://localhost:5500');
    } finally {
      setUrlLoading(false);
    }
  };

  const claimChecksToday = usage.claim_checks || 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20 group-hover:scale-105 transition-transform">
                <Shield className="w-5 h-5" />
              </div>
              <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
                TrustLens AI
              </span>
            </Link>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
              100% Free Access
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-slate-200">
                {displayName || user.email}
              </div>
              <div className="text-xs text-emerald-400 font-medium">
                Free &amp; Unlimited
              </div>
            </div>

            <form action={signoutAction}>
              <button
                type="submit"
                id="btn-signout"
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-medium transition-all shadow-sm"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </form>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome & Quota Overview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: User Profile info */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 relative overflow-hidden backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-cyan-400" /> Account Profile
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 uppercase font-bold">
                Free Forever
              </span>
            </div>
            <div className="space-y-2">
              <p className="text-xl font-bold text-white truncate">{displayName || 'User'}</p>
              <p className="text-xs text-slate-400 truncate">{user.email}</p>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span>Member since: {new Date(profile.created_at || '2026-01-01').toLocaleDateString()}</span>
              <button
                onClick={() => setIsEditingName(!isEditingName)}
                className="text-cyan-400 hover:text-cyan-300 underline font-medium"
              >
                {isEditingName ? 'Cancel' : 'Edit Name'}
              </button>
            </div>

            {isEditingName && (
              <form onSubmit={handleUpdateName} className="mt-3 space-y-2">
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white"
                  placeholder="Enter display name"
                />
                <button
                  type="submit"
                  disabled={isPending}
                  className="w-full py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium"
                >
                  Save Changes
                </button>
              </form>
            )}
            {nameMessage && (
              <p className="mt-2 text-xs text-cyan-300">{nameMessage}</p>
            )}
          </div>

          {/* Card 2: Daily Claim Checks (100% Free & Unlimited) */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 relative overflow-hidden backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-cyan-400" /> Today&apos;s Claims Checked
              </span>
              <span className="text-xs font-mono text-slate-400">{usage.day}</span>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-white">{claimChecksToday}</span>
              <span className="text-sm text-emerald-400 font-semibold">checks verified</span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>100% Free · Unlimited claim checks active</span>
            </div>
          </div>

          {/* Card 3: URL Security Scans */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 relative overflow-hidden backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-emerald-400" /> URL Scans Today
              </span>
              <span className="text-xs font-mono text-slate-400">{usage.day}</span>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-white">{usage.url_scans || 0}</span>
              <span className="text-sm text-slate-400">links scanned</span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed mt-3">
              Phishing, brand spoofing, high-risk TLDs and Web Risk engine scans recorded.
            </p>

            <div className="mt-5 pt-3 border-t border-slate-800/80 text-xs text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Zero URL browsing logs stored (FR-P5)
            </div>
          </div>
        </div>

        {/* Extension Token & Integration Card (FR-E8) */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-900/90 to-indigo-950/40 border border-slate-800 rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" /> Chrome Extension &amp; API Integration (FR-E8)
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Link your Chrome extension or API requests to your account using your Supabase session Bearer token.
              </p>
            </div>

            <button
              onClick={handleCopyToken}
              disabled={!sessionToken}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/20 transition-all disabled:opacity-50"
            >
              {tokenCopied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-300" />
                  <span>Token Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>Copy Auth Token</span>
                </>
              )}
            </button>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono text-xs text-slate-400 break-all select-all flex items-center justify-between gap-3">
            <span className="truncate">
              {sessionToken ? `Bearer ${sessionToken.slice(0, 32)}...${sessionToken.slice(-16)}` : 'Loading session token...'}
            </span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider flex-shrink-0">
              Valid Session
            </span>
          </div>

          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
            <span className="text-cyan-400 font-semibold">Tip:</span> Open Extension Options (or popup), paste this token, and all your browsing checks will synchronize with your dashboard quota.
          </div>
        </div>

        {/* Live Testing Workbench */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Claim Verification Test Widget */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Search className="w-4 h-4 text-cyan-400" /> Test Claim Verification
                </h3>
                <span className="text-xs text-slate-400">POST /api/verify</span>
              </div>

              <form onSubmit={handleTestClaim} className="space-y-3">
                <textarea
                  rows={3}
                  value={claimInput}
                  onChange={(e) => setClaimInput(e.target.value)}
                  placeholder="Enter a claim (e.g., '5G cellular towers spread respiratory viruses.')"
                  className="w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
                />

                <div className="flex justify-between items-center">
                  <div className="text-xs text-slate-500">
                    Cap: 5 claims / sentence splitting
                  </div>
                  <button
                    type="submit"
                    disabled={claimLoading || !claimInput.trim()}
                    className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                  >
                    {claimLoading ? 'Verifying...' : 'Verify Claim'}
                  </button>
                </div>
              </form>

              {claimError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  {claimError}
                </div>
              )}

              {claimResults && (
                <div className="mt-4 space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Results ({claimResults.length})
                  </div>
                  {claimResults.map((c, i) => (
                    <div
                      key={i}
                      className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-medium text-slate-200">{c.claim}</p>
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded font-bold uppercase ${
                            c.verdict === 'Verified'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : c.verdict === 'False' || c.verdict === 'Misleading'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {c.verdict}
                        </span>
                      </div>
                      {c.sources && c.sources.length > 0 ? (
                        <div className="text-[11px] text-slate-400 border-t border-slate-800/60 pt-2 space-y-1">
                          {c.sources.map((s: ClaimSource, j: number) => (
                            <div key={j} className="flex items-center justify-between">
                              <span>Source: {s.publisher} ({s.rating || s.verdict})</span>
                              {s.url && s.url !== '#' && (
                                <a
                                  href={s.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-cyan-400 hover:underline inline-flex items-center gap-1"
                                >
                                  Read <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-500">No external fact-check evidence indexed.</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* URL Safety Scanner Test Widget */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Globe className="w-4 h-4 text-emerald-400" /> Test URL Scanner
                </h3>
                <span className="text-xs text-slate-400">POST /api/scan</span>
              </div>

              <form onSubmit={handleTestUrl} className="space-y-3">
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://paypal-secure-login.xyz/claim"
                  className="w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                />

                <div className="flex justify-between items-center">
                  <div className="text-xs text-slate-500">
                    Local heuristics + Web Risk check
                  </div>
                  <button
                    type="submit"
                    disabled={urlLoading || !urlInput.trim()}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                  >
                    {urlLoading ? 'Scanning...' : 'Scan URL'}
                  </button>
                </div>
              </form>

              {urlError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  {urlError}
                </div>
              )}

              {urlResult && (
                <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-300 truncate max-w-[200px]">{urlResult.url}</span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded font-bold uppercase ${
                        urlResult.level === 'Safe'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : urlResult.level === 'Dangerous'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {urlResult.level}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400">
                    Source: <span className="text-slate-200">{urlResult.source}</span>
                  </div>

                  {urlResult.flags && urlResult.flags.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[11px] uppercase font-semibold text-amber-400">Heuristic Signals Detected:</div>
                      <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                        {urlResult.flags.map((flag: string, k: number) => (
                          <li key={k}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {urlResult.threats && urlResult.threats.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[11px] uppercase font-semibold text-rose-400">Threat Database Matches:</div>
                      <ul className="list-disc list-inside text-xs text-rose-300 space-y-0.5">
                        {urlResult.threats.map((threat: string, k: number) => (
                          <li key={k}>{threat}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Danger Zone: Account Deletion (FR-A11) */}
        <div className="border border-rose-900/30 bg-rose-950/10 rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-rose-300 flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-rose-400" /> Danger Zone: Account Deletion (FR-A11)
              </h3>
              <p className="text-xs text-rose-300/70 mt-1">
                Permanently delete your TrustLens profile and all daily usage count records. This action cannot be undone.
              </p>
            </div>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="px-4 py-2 rounded-xl bg-rose-600/80 hover:bg-rose-600 text-white text-xs font-semibold transition-all shadow-sm flex-shrink-0"
            >
              Delete Account
            </button>
          </div>

          {deleteError && (
            <p className="mt-3 text-xs text-rose-400">{deleteError}</p>
          )}
        </div>
      </main>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h4 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" /> Confirm Account Deletion
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed">
              Are you sure you want to permanently delete your account (<strong className="text-white">{user.email}</strong>)?
              All your profile data and usage records will be permanently removed.
            </p>
            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={isPending}
                className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-800 text-slate-200 text-xs font-medium hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={isPending}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all disabled:opacity-50"
              >
                {isPending ? 'Deleting...' : 'Yes, Delete My Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
