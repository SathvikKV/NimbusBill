"""Tests for NimbusBill FastAPI endpoints.

Uses FastAPI TestClient with a mocked Snowflake connection
so tests can run without a live Snowflake account.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date, datetime


# ── Mock the Snowflake connection before importing the app ─────────────────
def _make_mock_cursor(rows: list[dict]):
    """Create a mock cursor that returns the given rows."""
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    return cursor


def _make_mock_connection(rows: list[dict] | None = None):
    conn = MagicMock()
    cursor = _make_mock_cursor(rows or [])
    conn.cursor.return_value = cursor
    return conn


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    """Create a test client with mocked Snowflake."""
    with patch("api.main.get_connection") as mock_conn:
        mock_conn.return_value = _make_mock_connection([])
        from api.main import app
        yield TestClient(app)


@pytest.fixture
def client_with_data():
    """Create a test client that returns sample invoice data."""
    sample_invoices = [
        {
            "INVOICE_ID": "inv_test_001",
            "CUSTOMER_SK": 1,
            "CUSTOMER_NAME": "Acme Corp",
            "BILLING_PERIOD_START": date(2024, 1, 1),
            "BILLING_PERIOD_END": date(2024, 1, 31),
            "ISSUED_TS": datetime(2024, 2, 1, 4, 0, 0),
            "STATUS": "issued",
            "SUBTOTAL": 125.50,
            "TAX": 0.0,
            "TOTAL": 125.50,
            "CURRENCY": "USD",
        }
    ]
    with patch("api.main.get_connection") as mock_conn:
        mock_conn.return_value = _make_mock_connection(sample_invoices)
        from api.main import app
        yield TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# Health endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# ═══════════════════════════════════════════════════════════════════════════
# Invoice endpoints
# ═══════════════════════════════════════════════════════════════════════════

class TestInvoices:
    def test_list_invoices_returns_200(self, client):
        response = client.get("/invoices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_invoices_with_customer_filter(self, client):
        response = client.get("/invoices?customer_id=cust_1")
        assert response.status_code == 200

    def test_invoice_detail_not_found(self, client):
        response = client.get("/invoices/nonexistent_id")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# Customer endpoints
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomers:
    def test_list_customers_returns_200(self, client):
        response = client.get("/customers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_customer_usage_returns_200(self, client):
        response = client.get("/customers/cust_1/usage")
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_dashboard_summary_returns_200(self, client):
        response = client.get("/dashboard/summary")
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Usage endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestUsage:
    def test_usage_returns_200(self, client):
        response = client.get("/usage")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_usage_with_date_filter(self, client):
        response = client.get("/usage?date_from=2024-01-01&date_to=2024-01-31")
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline status
# ═══════════════════════════════════════════════════════════════════════════

class TestPipelineStatus:
    def test_pipeline_status_returns_200(self, client):
        response = client.get("/pipeline/status")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ═══════════════════════════════════════════════════════════════════════════
# Pricing endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestPricing:
    def test_pricing_returns_200(self, client):
        response = client.get("/pricing")
        assert response.status_code == 200
