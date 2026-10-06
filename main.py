"""TrustLens AI prototype backend: Truth Engine (Google Fact Check) + Safety Engine (Google Web Risk)."""
import os, re, time, hashlib
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

KEY = os.getenv("GOOGLE_API_KEY", "")
app = FastAPI(title="TrustLens AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
CACHE, HISTORY, BUCKET = {}, [], {}          # L1 cache, audit log, rate limiter (in-memory)

class Text(BaseModel): text: str
class Url(BaseModel): url: str

def limited(ip, cap=30, per=60):             # tiny token-bucket-style limiter
    now = time.time(); hits = [t for t in BUCKET.get(ip, []) if now - t < per]
    BUCKET[ip] = hits + [now]; return len(hits) >= cap

def split_claims(text):                       # naive atomic-claim splitter
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if len(p.split()) >= 4][:5] or [text.strip()[:200]]

def rate(r):
    r = r.lower()
    if re.search(r"false|fake|incorrect|misleading|pants|hoax|no evidence|wrong|scam", r): return "False"
    if re.search(r"true|correct|accurate|legit|confirmed", r): return "Verified"
    return "Mixed"

DEMO = {"vaccine": ("Misleading", "Demo Fact Checker", "Claim lacks context; no evidence supports it."),
        "5g": ("False", "Demo Fact Checker", "No scientific evidence links 5G to this.")}

async def check_claim(c):
    h = hashlib.md5(c.encode()).hexdigest()
    if h in CACHE: return {**CACHE[h], "cached": True}
    out = {"claim": c, "verdict": "Unverified", "sources": [], "cached": False}
    if KEY:                                   # LIVE: Google Fact Check Tools API
        async with httpx.AsyncClient(timeout=8) as cl:
            r = await cl.get("https://factchecktools.googleapis.com/v1alpha1/claims:search",
                             params={"query": c[:200], "key": KEY, "pageSize": 5})
        votes = []
        for cl_ in r.json().get("claims", []):
            for rv in cl_.get("claimReview", []):
                v = rate(rv.get("textualRating", "")); votes.append(v)
                out["sources"].append({"publisher": rv.get("publisher", {}).get("name"), "title": rv.get("title"),
                                       "rating": rv.get("textualRating"), "url": rv.get("url"), "verdict": v})
        if votes:
            top = max(set(votes), key=votes.count)
            out["verdict"], out["confidence"] = top, round(votes.count(top) / len(votes), 2)
    else:                                     # DEMO fallback so the UI works without a key
        for k, (v, p, t) in DEMO.items():
            if k in c.lower():
                out.update(verdict=v, confidence=0.9, sources=[{"publisher": p, "title": t, "rating": v, "url": "#", "verdict": v}])
    CACHE[h] = out; return out

@app.get("/api/health")
def health(): return {"mode": "live" if KEY else "demo", "cached": len(CACHE)}

@app.post("/api/verify")
async def verify(b: Text, req: Request):
    client_ip = req.client.host if req.client else "127.0.0.1"
    if limited(client_ip): raise HTTPException(429, "Rate limit hit")
    res = [await check_claim(c) for c in split_claims(b.text)]
    HISTORY.insert(0, {"type": "claim", "input": b.text[:80], "result": [x["verdict"] for x in res]})
    return {"claims": res}

BRANDS = ["paypal", "google", "amazon", "sbi", "hdfc", "paytm", "microsoft", "metamask", "binance"]

def heuristics(url):
    h = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower(); flags = []
    if re.fullmatch(r"[\d.]+", h): flags.append("IP address used as host")
    if "xn--" in h: flags.append("Punycode look-alike domain")
    if h.count("-") >= 2: flags.append("Many hyphens in domain")
    if h.rsplit(".", 1)[-1] in {"zip", "xyz", "top", "click", "tk", "ru"}: flags.append("High-risk TLD")
    if any(b in h and not h.endswith(b + ".com") for b in BRANDS): flags.append("Brand name inside unofficial domain")
    if re.search(r"airdrop|claim|wallet|verify|login|secure", h): flags.append("Urgency / crypto-drainer keyword")
    if url.startswith("http://"): flags.append("No HTTPS")
    return flags

@app.post("/api/scan")
async def scan(b: Url, req: Request):
    client_ip = req.client.host if req.client else "127.0.0.1"
    if limited(client_ip): raise HTTPException(429, "Rate limit hit")
    flags, threats, source = heuristics(b.url), [], "heuristics"
    if KEY:                                   # LIVE: Google Web Risk API
        async with httpx.AsyncClient(timeout=8) as cl:
            r = await cl.get("https://webrisk.googleapis.com/v1/uris:search", params=[
                ("uri", b.url), ("key", KEY), ("threatTypes", "MALWARE"),
                ("threatTypes", "SOCIAL_ENGINEERING"), ("threatTypes", "UNWANTED_SOFTWARE")])
        threats, source = r.json().get("threat", {}).get("threatTypes", []), "Google Web Risk + heuristics"
    level = "Dangerous" if threats else "Suspicious" if len(flags) >= 2 else "Caution" if flags else "Safe"
    HISTORY.insert(0, {"type": "url", "input": b.url[:80], "result": [level]})
    return {"url": b.url, "level": level, "threats": threats, "flags": flags, "source": source}

@app.get("/api/history")
def history(): return HISTORY[:15]

app.mount("/", StaticFiles(directory="static", html=True), name="static")
