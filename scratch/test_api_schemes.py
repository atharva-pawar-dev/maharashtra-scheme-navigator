from fastapi.testclient import TestClient
from scheme_navigator.api.main import app

c = TestClient(app)
res = c.get("/canonical-schemes")
schemes = res.json()
print("Total schemes from /canonical-schemes:", len(schemes))
s0 = schemes[0]
print("Scheme 0 keys:", list(s0.keys()))
print("is_decision_ready in scheme 0:", s0.get("is_decision_ready"))
print("public_status_category in scheme 0:", s0.get("public_status_category"))

ready = [s for s in schemes if s.get("is_decision_ready") is True or s.get("public_status_category") == "DECISION_READY"]
print("Ready schemes count:", len(ready))
for r in ready[:5]:
    print(" - Ready:", r.get("canonical_scheme_id"), "| pub_status_cat:", r.get("public_status_category"))
