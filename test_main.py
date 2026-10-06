from fastapi.testclient import TestClient
import main
c = TestClient(main.app)

def test_health():
    assert c.get("/api/health").json()["mode"] in ("live", "demo")

def test_scan_flags_lookalike():
    r = c.post("/api/scan", json={"url": "http://paypal-secure-login.xyz/claim"}).json()
    assert r["level"] in ("Suspicious", "Dangerous")

def test_verify_returns_claims():
    assert "claims" in c.post("/api/verify", json={"text": "5G towers spread viruses quickly."}).json()

if __name__ == "__main__":
    test_health()
    test_scan_flags_lookalike()
    test_verify_returns_claims()
    print("All tests passed!")

