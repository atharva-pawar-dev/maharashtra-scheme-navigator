from fastapi import FastAPI
from fastapi.testclient import TestClient

from scheme_navigator.api.reviewer_ui import router


def test_reviewer_dashboard_route_serves_html() -> None:
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/reviewer")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Scheme Navigator" in response.text
    assert "documents/audit-upload" in response.text
    assert "documents/reviews" in response.text
