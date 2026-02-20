"""Tests for data generation scripts.

Validates that the generated usage events, customers, and pricing data
conform to expected schemas and business rules.
"""
import json
import os
import tempfile
import pytest

# ── Import generators ──────────────────────────────────────────────────────
from datagen.generate_usage_events import generate_events, save_events
from datagen.generate_customers import generate_customers, save_customers
from datagen.generate_pricing import generate_pricing, PRICING_RULES


# ═══════════════════════════════════════════════════════════════════════════
# Usage Events
# ═══════════════════════════════════════════════════════════════════════════

class TestUsageEventGeneration:
    """Test the usage event generator."""

    def test_generates_correct_number_of_events(self):
        """Each customer should produce approximately the requested number of events."""
        events = generate_events("2024-01-15", num_customers=5, events_per_customer=10,
                                 late_prob=0, duplicate_prob=0)
        # With 0 duplicate prob, should be ~50 events (5 * 10 ± gaussian noise)
        assert 20 <= len(events) <= 80, f"Expected ~50 events, got {len(events)}"

    def test_event_schema_fields(self):
        """Every event must have the required fields."""
        required_fields = {
            "event_id", "event_timestamp", "customer_id", "product_id",
            "plan_id", "quantity", "unit", "region", "schema_version"
        }
        events = generate_events("2024-01-15", num_customers=2, events_per_customer=3,
                                 late_prob=0, duplicate_prob=0)
        for event in events:
            missing = required_fields - set(event.keys())
            assert not missing, f"Event missing fields: {missing}"

    def test_event_id_is_uuid(self):
        """event_id should be a valid UUID string."""
        events = generate_events("2024-01-15", num_customers=1, events_per_customer=1,
                                 late_prob=0, duplicate_prob=0)
        import uuid
        for event in events:
            try:
                uuid.UUID(event["event_id"])
            except ValueError:
                pytest.fail(f"Invalid UUID: {event['event_id']}")

    def test_quantity_is_positive(self):
        """Quantity should always be positive (abs is applied)."""
        events = generate_events("2024-01-15", num_customers=5, events_per_customer=20,
                                 late_prob=0, duplicate_prob=0)
        for event in events:
            assert event["quantity"] >= 0, f"Negative quantity: {event['quantity']}"

    def test_duplicate_injection(self):
        """With 100% duplicate probability, events should contain duplicates."""
        events = generate_events("2024-01-15", num_customers=3, events_per_customer=5,
                                 late_prob=0, duplicate_prob=1.0)
        event_ids = [e["event_id"] for e in events]
        # With 100% dup prob, every event is duplicated → ~double the count
        assert len(event_ids) > len(set(event_ids)), "Expected duplicates but found none"

    def test_late_arrival_injection(self):
        """With 100% late probability, all timestamps should precede the target date."""
        from datetime import datetime
        events = generate_events("2024-06-15", num_customers=2, events_per_customer=5,
                                 late_prob=1.0, duplicate_prob=0)
        target = datetime(2024, 6, 15)
        for event in events:
            ts = datetime.fromisoformat(event["event_timestamp"].replace("Z", ""))
            assert ts < target, f"Expected late event before {target}, got {ts}"

    def test_save_creates_jsonl_file(self):
        """save_events should create a valid JSONL file."""
        events = generate_events("2024-01-15", num_customers=2, events_per_customer=2,
                                 late_prob=0, duplicate_prob=0)
        with tempfile.TemporaryDirectory() as tmpdir:
            save_events(events, "2024-01-15", tmpdir)
            filepath = os.path.join(tmpdir, "usage_events_2024-01-15.jsonl")
            assert os.path.exists(filepath)

            with open(filepath) as f:
                lines = f.readlines()
            assert len(lines) == len(events)
            # Each line should be valid JSON
            for line in lines:
                parsed = json.loads(line)
                assert "event_id" in parsed

    def test_valid_product_ids(self):
        """product_id should be one of the known products."""
        valid_products = {"prod_api_requests", "prod_storage_gb", "prod_compute_minutes", "prod_ai_tokens"}
        events = generate_events("2024-01-15", num_customers=3, events_per_customer=10,
                                 late_prob=0, duplicate_prob=0)
        for event in events:
            assert event["product_id"] in valid_products, f"Unknown product: {event['product_id']}"

    def test_unit_matches_product(self):
        """The unit field should match the expected unit for the product."""
        unit_map = {
            "prod_api_requests": "requests",
            "prod_storage_gb": "gb_month",
            "prod_compute_minutes": "minutes",
            "prod_ai_tokens": "tokens",
        }
        events = generate_events("2024-01-15", num_customers=3, events_per_customer=10,
                                 late_prob=0, duplicate_prob=0)
        for event in events:
            expected_unit = unit_map[event["product_id"]]
            assert event["unit"] == expected_unit, f"Unit mismatch for {event['product_id']}"


# ═══════════════════════════════════════════════════════════════════════════
# Pricing
# ═══════════════════════════════════════════════════════════════════════════

class TestPricingGeneration:
    """Test the pricing catalog generator."""

    def test_generates_csv_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_pricing(tmpdir)
            filepath = os.path.join(tmpdir, "pricing_catalog.csv")
            assert os.path.exists(filepath)

    def test_csv_has_header_and_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_pricing(tmpdir)
            filepath = os.path.join(tmpdir, "pricing_catalog.csv")
            with open(filepath) as f:
                lines = f.readlines()
            # Header + N pricing rules
            assert len(lines) == 1 + len(PRICING_RULES)

    def test_csv_header_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_pricing(tmpdir)
            filepath = os.path.join(tmpdir, "pricing_catalog.csv")
            with open(filepath) as f:
                header = f.readline().strip()
            expected = "rate_id,product_id,plan_id,unit,unit_price,currency,effective_from,effective_to"
            assert header == expected

    def test_prices_are_non_negative(self):
        for rule in PRICING_RULES:
            assert rule["price"] >= 0, f"Negative price for {rule['product_id']}/{rule['plan_id']}"


# ═══════════════════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomerGeneration:
    """Test the customer generator."""

    def test_generates_jsonl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            customers = generate_customers("2024-01-15", 5)
            save_customers(customers, "2024-01-15", tmpdir)
            files = [f for f in os.listdir(tmpdir) if f.startswith("customers_")]
            assert len(files) == 1

    def test_correct_number_of_customers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            customers = generate_customers("2024-01-15", 7)
            save_customers(customers, "2024-01-15", tmpdir)
            files = [f for f in os.listdir(tmpdir) if f.startswith("customers_")]
            filepath = os.path.join(tmpdir, files[0])
            with open(filepath) as f:
                lines = f.readlines()
            assert len(lines) == 7

    def test_customer_schema(self):
        required_fields = {"customer_id", "customer_name", "plan_id", "status", "country"}
        customers = generate_customers("2024-01-15", 3)
        for customer in customers:
            missing = required_fields - set(customer.keys())
            assert not missing, f"Customer missing fields: {missing}"
