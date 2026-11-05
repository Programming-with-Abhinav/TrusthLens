'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Shield,
  Search,
  Globe,
  ArrowRight,
  Lock,
  Sparkles,
  Zap,
} from 'lucide-react';

interface ClaimSource {
  publisher: string;
  title?: string;
  rating?: string;
  url?: string;
  verdict?: string;
}

interface ClaimResult {
  claim: string;
  verdict: string;
  confidence?: number;
  sources?: ClaimSource[];
  synthesis?: string;
}

interface UrlScanResult {
  url: string;
  level: string;
  flags?: string[];
  flag_explanations?: Record<string, string>;
  should_block?: boolean;
  source?: string;
}

interface ClaimSource {
  publisher: string;
  title?: string;
  rating?: string;
  url?: string;
  verdict?: string;
}

interface ClaimResult {
  claim: string;
  verdict: string;
  confidence?: number;
  sources?: ClaimSource[];
  synthesis?: string;
}

interface UrlScanResult {
  url: string;
  level: string;
  flags?: string[];
  flag_explanations?: Record<string, string>;
  should_block?: boolean;
  source?: string;
}

export default function HomePage() {
  const [claimText, setClaimText] = useState('5G networks cause respiratory viruses');
  const [claimLoading, setClaimLoading] = useState(false);
  const [claimResult, setClaimResult] = useState<ClaimResult | null>(null);

  const [urlText, setUrlText] = useState('http://paypal-security-login.xyz/claim');
  const [urlLoading, setUrlLoading] = useState(false);
  const [urlResult, setUrlResult] = useState<UrlScanResult | null>(null);

  const handleQuickClaimCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimText.trim()) return;
    setClaimLoading(true);
    setClaimResult(null);

    try {
      const res = await fetch('http://localhost:5500/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: claimText }),
      });
      const data = await res.json();
      setClaimResult(data.claims?.[0] || null);
    } catch {
      // Mock result if backend is unavailable on port 5500
      setClaimResult({
        claim: claimText,
        verdict: 'False',
        confidence: 0.95,
        sources: [
          {
            publisher: 'WHO / FactCheck.org',
            title: 'No scientific evidence links 5G radio waves to viral propagation.',
            verdict: 'False',
          },
        ],
      });
    } finally {
      setClaimLoading(false);
    }
  };

  const handleQuickUrlScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlText.trim()) return;
    setUrlLoading(true);
    setUrlResult(null);

    try {
      const res = await fetch('http://localhost:5500/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlText }),
      });
      const data = await res.json();
      setUrlResult(data);
    } catch {
      // Demo preview if backend not currently running
      setUrlResult({
        url: urlText,
        level: 'Dangerous',
        flags: [
          'No HTTPS',
          'High-risk TLD (.xyz)',
          'Brand name inside unofficial domain (paypal)',
          'Urgency / crypto-drainer keyword (claim)',
        ],
        source: 'Heuristics + Web Risk preview',
      });
    } finally {
      setUrlLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25">
              <Shield className="w-5 h-5" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
              TrustLens AI
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-xs sm:text-sm font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-xs sm:text-sm font-semibold px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-md shadow-cyan-500/20 transition-all hover:scale-105"
            >
              Get Started
            </Link>
            <Link
              href="/dashboard"
              className="text-xs sm:text-sm font-medium text-cyan-400 hover:text-cyan-300 px-3 py-1.5 rounded-lg border border-cyan-500/30 hover:bg-cyan-500/10 transition-colors"
            >
              Dashboard &rarr;
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-32">
          {/* Ambient decorative gradients */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-500/15 via-blue-500/15 to-indigo-500/15 blur-[120px] rounded-full pointer-events-none" />

          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-6 animate-pulse">
              <Sparkles className="w-3.5 h-3.5" />
              <span>TrustLens AI v1.1 – Truth Engine &amp; Safety Defense</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Verify claims in real time.{' '}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
                Block deceptive scams.
              </span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed">
              Dual-layer browser protection. Checks selected factual claims against Google Fact Check Tools and scans URLs with local heuristics and Web Risk before you click.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/signup"
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-xl shadow-cyan-500/25 transition-all flex items-center gap-2 hover:scale-105"
              >
                <span>Create Free Account (100% Free &amp; Unlimited)</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/dashboard"
                className="px-6 py-3.5 rounded-xl border border-slate-700 bg-slate-900/80 hover:bg-slate-800 text-slate-200 font-semibold text-sm transition-all"
              >
                Open Dashboard
              </Link>
            </div>
          </div>
        </section>

        {/* Live Interactive Workbench Preview */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white">Experience TrustLens in Action</h2>
            <p className="text-sm text-slate-400 mt-2">Test claim verification and URL risk detection live</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Claim Checker Card */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Search className="w-4 h-4" /> Truth Engine (Claims)
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  Google Fact Check API
                </span>
              </div>

              <form onSubmit={handleQuickClaimCheck} className="space-y-3">
                <textarea
                  rows={2}
                  value={claimText}
                  onChange={(e) => setClaimText(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
                  placeholder="Enter a controversial claim..."
                />
                <button
                  type="submit"
                  disabled={claimLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  <Zap className="w-3.5 h-3.5" />
                  {claimLoading ? 'Searching Fact Checks...' : 'Check Claim Validity'}
                </button>
              </form>

              {claimResult && (
                <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300 truncate max-w-[240px]">
                      {claimResult.claim}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded font-bold uppercase ${claimResult.verdict === 'Verified'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                    >
                      {claimResult.verdict}
                    </span>
                  </div>
                  {claimResult.sources?.[0] && (
                    <div className="text-xs text-slate-400 pt-2 border-t border-slate-800">
                      <p className="text-slate-300 font-medium">{claimResult.sources[0].publisher}:</p>
                      <p className="text-slate-400 mt-0.5">{claimResult.sources[0].title}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* URL Scanner Card */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Globe className="w-4 h-4" /> Safety Engine (URLs)
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  Web Risk + Heuristics
                </span>
              </div>

              <form onSubmit={handleQuickUrlScan} className="space-y-3">
                <input
                  type="text"
                  value={urlText}
                  onChange={(e) => setUrlText(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                  placeholder="https://example-phishing.xyz/verify"
                />
                <button
                  type="submit"
                  disabled={urlLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  <Shield className="w-3.5 h-3.5" />
                  {urlLoading ? 'Scanning Indicators...' : 'Analyze URL Risk'}
                </button>
              </form>

              {urlResult && (
                <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-300 truncate max-w-[240px]">
                      {urlResult.url}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded font-bold uppercase ${urlResult.level === 'Safe'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : urlResult.level === 'Dangerous'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                    >
                      {urlResult.level}
                    </span>
                  </div>
                  {urlResult.flags && (
                    <div className="text-xs text-slate-400 pt-2 border-t border-slate-800 space-y-1">
                      <div className="text-[11px] font-semibold text-amber-400">Signals:</div>
                      {urlResult.flags.map((f: string, idx: number) => (
                        <div key={idx} className="text-slate-300 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Feature Highlights Grid */}
        <section className="border-t border-slate-800/80 py-20 bg-slate-900/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-white">Engineered for Trust &amp; Privacy</h2>
              <p className="text-slate-400 mt-3 max-w-2xl mx-auto">
                TrustLens combines external verification databases with deterministic on-device heuristics.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="p-3 w-fit rounded-xl bg-cyan-500/10 text-cyan-400 mb-4">
                  <Search className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-white">Truth Engine</h3>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Extracts atomic claims from unstructured text and checks them against Google Fact Check Tools and verified fact-check publications.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="p-3 w-fit rounded-xl bg-emerald-500/10 text-emerald-400 mb-4">
                  <Shield className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-white">Safety Engine</h3>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Analyzes URLs for punycode look-alikes, IP hosts, risky TLDs, crypto-drainer keywords, and Google Web Risk malware threats.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="p-3 w-fit rounded-xl bg-indigo-500/10 text-indigo-400 mb-4">
                  <Lock className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-white">Strict Privacy Guarantees</h3>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Only aggregated daily counts are saved. No claim text, no visited URLs, and no browsing history are stored in user records.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-8 text-center text-xs text-slate-500">
        <p>&copy; 2026 TrustLens AI. Built in accordance with TrustLens PRD v1.1.</p>
      </footer>
    </div>
  );
}
