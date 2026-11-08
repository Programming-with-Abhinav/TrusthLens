export interface ClaimSource {
  publisher: string;
  title?: string;
  rating?: string;
  url?: string;
  verdict: string;
}

export interface ClaimItem {
  claim: string;
  verdict: 'True' | 'MostlyTrue' | 'Mixed' | 'Misleading' | 'False' | 'Unverified' | 'Unrated' | string;
  confidence?: number;
  stance?: string;
  synthesis?: string;
  sources?: ClaimSource[];
  source?: string;
  cached?: boolean;
}

export interface VerifyResponse {
  claims: ClaimItem[];
}

export interface FlagExplanation {
  flag: string;
  explanation: string;
}

export interface ScanResponse {
  url: string;
  level: 'Safe' | 'Caution' | 'Suspicious' | 'Dangerous' | string;
  threats?: string[];
  flags?: string[];
  flag_explanations?: FlagExplanation[] | Record<string, string>;
  telemetry?: Record<string, unknown>;
  should_block?: boolean;
  source?: string;
}
