"""TrustLens AI - Advanced Truth Engine (Phase 2).
Implements:
- FR-C7: Semantic Hybrid Retrieval (BM25 + Dense Vector Cosine Similarity) over ClaimReview records
- FR-C8: NLI Stance Classification & Composite Trust Scoring (with temporal decay & source weights)
- FR-C9: Grounded Evidence Synthesis (Gemini API with sanitization & fallback)
"""
import os
import re
import math
import datetime
from typing import List, Dict, Any, Optional
import httpx

# Pre-seeded ClaimReview repository across diverse domains (health, science, technology, finance, crypto, security)
SEED_CLAIM_REVIEWS: List[Dict[str, Any]] = [
    {
        "id": "cr-001",
        "claim": "5G cell towers spread viral respiratory infections and weaken human immune defenses.",
        "rating": "False",
        "publisher": "Health Feedback & WHO",
        "authority_weight": 0.95,
        "date": "2023-01-15",
        "url": "https://healthfeedback.org/claimreview/5g-radio-waves-do-not-spread-viral-illnesses/",
        "summary": "Extensive peer-reviewed biophysical studies show radio frequency electromagnetic radiation from 5G telecom towers cannot produce, transmit, or enhance viral pathogens."
    },
    {
        "id": "cr-002",
        "claim": "mRNA vaccines alter human DNA and insert trackable biometric microchips.",
        "rating": "False",
        "publisher": "Reuters Fact Check",
        "authority_weight": 0.95,
        "date": "2023-06-20",
        "url": "https://www.reuters.com/fact-check/mrna-vaccines-do-not-alter-human-dna/",
        "summary": "mRNA vaccines deliver temporary instructions to ribosomal proteins in the cytoplasm and never enter the cell nucleus where genomic DNA resides."
    },
    {
        "id": "cr-003",
        "claim": "Drinking colloidal silver or alkaline water completely cures viral infections.",
        "rating": "False",
        "publisher": "Mayo Clinic & PolitiFact",
        "authority_weight": 0.90,
        "date": "2022-11-10",
        "url": "https://www.politifact.com/factchecks/2022/colloidal-silver-cure-myth/",
        "summary": "Medical regulators confirm colloidal silver has no proven efficacy against viral pathogens and carries toxic risks including argyria and kidney impairment."
    },
    {
        "id": "cr-004",
        "claim": "MetaMask and cryptocurrency wallets require urgent KYC re-verification to prevent immediate asset burning.",
        "rating": "Scam / False",
        "publisher": "TrustLens Security Intel",
        "authority_weight": 0.92,
        "date": "2024-03-01",
        "url": "https://trustlens.ai/advisories/crypto-kyc-wallet-phishing/",
        "summary": "Non-custodial cryptocurrency software wallets do not conduct KYC procedures. All emails or links demanding verification are phishing attempts designed to steal seed phrases."
    },
    {
        "id": "cr-005",
        "claim": "NASA confirmed the Earth will experience six continuous days of total darkness.",
        "rating": "False",
        "publisher": "Snopes",
        "authority_weight": 0.90,
        "date": "2021-08-14",
        "url": "https://www.snopes.com/fact-check/six-days-of-darkness/",
        "summary": "NASA has repeatedly debunked claims of a solar storm causing global planetary darkness; the claim originated from a satirical website."
    },
    {
        "id": "cr-006",
        "claim": "Fluoride in tap water at regulated dental levels causes immediate cognitive decline in children.",
        "rating": "Mixed",
        "publisher": "FactCheck.org",
        "authority_weight": 0.88,
        "date": "2024-02-18",
        "url": "https://www.factcheck.org/fluoride-drinking-water-scientific-review/",
        "summary": "Systematic reviews find dental community levels of water fluoridation (0.7 mg/L) are safe; potential neurotoxicity observed only at extreme concentrations exceeding 1.5 mg/L."
    },
    {
        "id": "cr-007",
        "claim": "Artificial Intelligence models consume more electricity per day than the entire global airline network.",
        "rating": "False",
        "publisher": "MIT Technology Review / AP Fact Check",
        "authority_weight": 0.93,
        "date": "2024-05-12",
        "url": "https://apnews.com/article/ai-data-center-energy-consumption-fact-check/",
        "summary": "While AI datacenter electricity demand is growing rapidly, data centers globally represent approximately 1-2% of global electricity, far below the global aviation sector."
    }
]

# Source Authority Weighting Directory (FR-C8)
SOURCE_AUTHORITY = {
    "reuters": 0.98,
    "associated press": 0.98,
    "ap news": 0.98,
    "who": 0.96,
    "world health organization": 0.96,
    "politifact": 0.92,
    "snopes": 0.91,
    "factcheck.org": 0.92,
    "health feedback": 0.94,
    "google": 0.90,
    "demo": 0.85
}

def get_source_authority(publisher_name: str) -> float:
    pub_lower = publisher_name.lower()
    for key, weight in SOURCE_AUTHORITY.items():
        if key in pub_lower:
            return weight
    return 0.80

def tokenize(text: str) -> List[str]:
    """Basic NLP tokenization and normalization."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "and", "or", "in", "on", "at",
        "to", "for", "with", "that", "this", "it", "from", "by", "as", "be", "of"
    }
    tokens = [t for t in cleaned.split() if len(t) >= 3 and t not in stop_words]
    return tokens

def build_vector_representation(tokens: List[str], vocab: List[str]) -> List[float]:
    """Generates a dense normalized frequency vector over vocabulary."""
    vec = [0.0] * len(vocab)
    if not tokens:
        return vec
    for t in tokens:
        if t in vocab:
            vec[vocab.index(t)] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))

def compute_bm25_score(query_tokens: List[str], doc_tokens: List[str], avgdl: float, k1: float = 1.5, b: float = 0.75) -> float:
    """Computes BM25 keyword matching score."""
    score = 0.0
    doc_len = len(doc_tokens)
    for q in query_tokens:
        tf = doc_tokens.count(q)
        if tf > 0:
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / (avgdl or 1.0)))
            score += (numerator / denominator)
    return score

class SemanticTruthEngine:
    """Hybrid Retrieval Engine implementing BM25 + Dense Cosine Similarity and RRF."""
    def __init__(self, records: List[Dict[str, Any]] = SEED_CLAIM_REVIEWS):
        self.records = records
        self._build_index()

    def _build_index(self) -> None:
        all_tokens: List[str] = []
        for r in self.records:
            t: List[str] = tokenize(f"{r['claim']} {r['summary']}")
            r["_tokens"] = t
            all_tokens.extend(t)
        self.vocab: List[str] = sorted(set(all_tokens))
        self.avgdl = sum(len(r["_tokens"]) for r in self.records) / max(len(self.records), 1)
        for r in self.records:
            r["_vec"] = build_vector_representation(r["_tokens"], self.vocab)

    def hybrid_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion (RRF) between Dense Vector Similarity and BM25.

        Guard against weak or unrelated matches: no meaningful token overlap means the
        claim is not evidence-backed and should not be treated as a real fact-check hit.
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        q_set = set(q_tokens)
        q_vec = build_vector_representation(q_tokens, self.vocab)

        # 1. Rank by Dense Vector Similarity
        vector_ranked = sorted(
            self.records,
            key=lambda r: cosine_similarity(q_vec, r["_vec"]),
            reverse=True
        )

        # 2. Rank by BM25
        bm25_ranked = sorted(
            self.records,
            key=lambda r: compute_bm25_score(q_tokens, r["_tokens"], self.avgdl),
            reverse=True
        )

        # 3. Reciprocal Rank Fusion (RRF score: 1 / (60 + rank))
        rrf_scores: Dict[str, float] = {}
        coverage: Dict[str, int] = {}

        for rank, r in enumerate(vector_ranked):
            overlap = len(q_set & set(r["_tokens"]))
            if overlap == 0:
                continue
            sim = cosine_similarity(q_vec, r["_vec"])
            if sim > 0.08:
                rrf_scores[r["id"]] = rrf_scores.get(r["id"], 0.0) + (1.0 / (60 + rank))
                coverage[r["id"]] = max(coverage.get(r["id"], 0), overlap)

        for rank, r in enumerate(bm25_ranked):
            overlap = len(q_set & set(r["_tokens"]))
            if overlap == 0:
                continue
            bm_score = compute_bm25_score(q_tokens, r["_tokens"], self.avgdl)
            if bm_score > 0.1:
                rrf_scores[r["id"]] = rrf_scores.get(r["id"], 0.0) + (1.0 / (60 + rank))
                coverage[r["id"]] = max(coverage.get(r["id"], 0), overlap)

        # Filter and return top_k. Unrelated claims with no semantic overlap must not be treated
        # as evidence-backed matches, even when a weak similarity score is non-zero.
        candidates = [r for r in self.records if r["id"] in rrf_scores and coverage.get(r["id"], 0) >= 2]
        candidates.sort(key=lambda r: rrf_scores[r["id"]], reverse=True)
        return candidates[:top_k]

# Global singleton
TRUTH_ENGINE = SemanticTruthEngine()

def classify_nli_stance(claim_text: str, evidence_text: str, rating_verdict: str) -> str:
    """NLI Stance Classification (Supports, Refutes, Neutral/Mixed).
    FR-C8 requirement.
    """
    e_lower = evidence_text.lower()
    r_lower = rating_verdict.lower()

    if "false" in r_lower or "scam" in r_lower or "hoax" in r_lower or "debunked" in r_lower:
        # The evidence refutes the claim
        return "Refutes"
    elif "verified" in r_lower or "true" in r_lower or "accurate" in r_lower:
        # The evidence supports the claim
        return "Supports"
    elif re.search(r"cannot|no evidence|myth|alter.*not|debunk", e_lower):
        return "Refutes"
    elif re.search(r"confirms|valid|consistent|proves", e_lower):
        return "Supports"
    return "Neutral"

def compute_temporal_decay(published_date_str: Optional[str]) -> float:
    """Computes temporal decay factor: older evidence decays slightly in recency weight."""
    if not published_date_str:
        return 0.90
    try:
        # Parse YYYY-MM-DD
        dt = datetime.datetime.strptime(published_date_str[:10], "%Y-%m-%d")
        days_ago = (datetime.datetime.now() - dt).days
        # Half-life of approximately 4 years (~1460 days), minimum floor at 0.70
        decay = math.exp(-0.00025 * max(days_ago, 0))
        return max(round(decay, 3), 0.70)
    except Exception:
        return 0.88

def compute_composite_trust_score(
    verdict: str,
    stance: str,
    sources: List[Dict[str, Any]],
    date_str: Optional[str] = None
) -> float:
    """Computes composite truth score (0.0 to 100.0) based on verdict, stance,
    source authority weighting, and temporal decay (FR-C8).
    """
    if verdict == "No evidence found":
        return 50.0

    # Base truth direction
    if verdict == "Verified" or stance == "Supports":
        base_score = 92.0
    elif verdict in ("False", "Misleading") or stance == "Refutes":
        base_score = 8.0
    else:
        base_score = 48.0

    # Calculate average source authority
    if sources:
        auth_scores = [get_source_authority(s.get("publisher", "")) for s in sources]
        avg_auth = sum(auth_scores) / len(auth_scores)
    else:
        avg_auth = 0.80

    temporal_factor = compute_temporal_decay(date_str)

    # Adjust towards certainty according to authority and time
    confidence_weight = avg_auth * temporal_factor
    adjusted_score = base_score * confidence_weight + (50.0 * (1.0 - confidence_weight))
    return round(max(min(adjusted_score, 100.0), 0.0), 1)

async def synthesize_grounded_explanation(
    claim: str,
    verdict: str,
    stance: str,
    sources: List[Dict[str, Any]]
) -> str:
    """Grounded LLM Evidence Synthesis (FR-C9).
    Constrained strictly to retrieved evidence with inline citations.
    Falls back gracefully to evidence quotes if Gemini key is absent.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    if not sources or verdict == "Unverified" or verdict == "No evidence found":
        return "No authoritative fact-checking record or peer-reviewed evidence was found for this claim."

    evidence_context: List[str] = []
    for s in sources[:3]:
        pub = str(s.get("publisher") or "Source")
        summary = str(s.get("title") or s.get("summary") or "Evaluated claim.")
        evidence_context.append(f"- {pub}: \"{summary}\"")
    context_str = "\n".join(evidence_context)

    # If Gemini API key is available, generate grounded explanation
    if gemini_key:
        try:
            # Input sanitization against prompt injection
            sanitized_claim = re.sub(r"[\n\r\"']", " ", claim)[:200]
            prompt = (
                "You are TrustLens AI, a factual verification engine. Provide a concise explanation of the verdict "
                "using only the provided evidence, and for a false or misleading claim state the accurate fact "
                "that the evidence supports. Include the publisher name. If the evidence does not establish a "
                "correction, say so and direct the reader to the cited review; do not invent facts.\n\n"
                f"Claim: {sanitized_claim}\n"
                f"Verdict: {verdict} (Stance: {stance})\n"
                f"Evidence:\n{context_str}\n\nSynthesis:"
            )

            async with httpx.AsyncClient(timeout=6.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
                payload: Dict[str, Any] = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100}
                }
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    cand = res.json().get("candidates", [])
                    if cand and cand[0].get("content", {}).get("parts"):
                        return cand[0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    # Deterministic fallback synthesis grounded directly in sources
    primary = sources[0]
    pub = primary.get("publisher", "Independent fact-checkers")
    summary = primary.get("title") or primary.get("summary") or "No further details."
    return f"According to {pub}, this statement is rated {verdict}. The cited fact-check reports: {summary}"
