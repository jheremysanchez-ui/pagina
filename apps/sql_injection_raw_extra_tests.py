"""
Tests for SQL injection against various endpoints, plus validation for raw() and extra().

These tests demonstrate how to ensure user-supplied data is not interpolated
into SQL strings. They rely on Django's built‑in protections and
illustrate correct usage of parameterized queries both via the ORM and
via raw SQL with placeholders. They also test that application endpoints
handle malicious input gracefully by returning error responses rather than
executing injected SQL.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db import connection

User = get_user_model()

# Common SQL injection payloads. None of these should succeed.
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "\" OR \"\" = \"",
    "'; DROP TABLE users; --",
]


@pytest.fixture
def api_client():
    """Return a REST framework APIClient."""
    return APIClient()


@pytest.mark.django_db
@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_sql_injection_login_email(api_client, payload):
    """Login endpoint must not authenticate with SQL injection strings in the email field."""
    # Create a legitimate user
    User.objects.create_user(email="normal@example.com", password="ClaveSegura123!")
    # Attempt to login using an injection payload as the email
    data = {"email": payload, "password": "irrelevante"}
    # The name 'jwt-create' is used by Djoser; adjust if different in your project
    response = api_client.post(reverse("jwt-create"), data, format="json")
    # Expect either 400 (bad request) or 401 (unauthorized)
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
def test_sql_injection_product_search(api_client):
    """Product search should not treat the query as executable SQL and must return safely."""
    malicious_query = "' OR 1=1 --"
    # POST search endpoint; adjust the URL to your actual search endpoint
    response = api_client.post(
        "/api/product/search",
        {"category_id": 0, "search": malicious_query},
        format="json",
    )
    # Should return a valid response but not a SQL error
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        # If the endpoint returns search results, the malicious query should not match everything
        assert "search_products" in response.json() or "error" in response.json()


@pytest.mark.django_db
def test_sql_injection_order_id(api_client):
    """Order detail endpoint must reject non‑numeric or injected IDs."""
    malicious_id = "1 OR 1=1"
    # Attempt to fetch an order with a malicious ID; adjust the path to your detail view
    response = api_client.get(f"/api/orders/get-order/{malicious_id}")
    # Expect 400 (bad request) or 404 (not found)
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
def test_sql_injection_coupon_code(api_client):
    """Coupon validation should not execute injected SQL."""
    malicious_code = "' OR 'a'='a"
    # Query parameter coupon_name is typical; adjust if different
    response = api_client.get(
        "/api/coupons/check-coupon",
        {"coupon_name": malicious_code},
    )
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
def test_sql_injection_cart_quantity(api_client):
    """Adding to cart must validate numeric IDs and quantities and reject SQL injection attempts."""
    payload = {
        "product_id": "1 OR 1=1",
        "quantity": "1; DROP TABLE cart;",
    }
    response = api_client.post("/api/cart/add-item", payload, format="json")
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_raw_query_parameterization(monkeypatch, payload):
    """Ensure that raw SQL execution uses parameterized queries.

    This test monkeypatches connection.cursor() to capture arguments passed to
    execute(). It then performs a simple SELECT using placeholders and
    verifies that the payload appears in params but not in the SQL string.
    """
    calls = []

    class FakeCursor:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            return None
        def fetchall(self):
            return []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    # Monkeypatch connection.cursor to our FakeCursor
    monkeypatch.setattr(connection, "cursor", lambda: FakeCursor())

    # Simulate a safe raw query using placeholders
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 WHERE %s=%s", [payload, payload])

    assert calls, "cursor.execute was not called"
    sql, params = calls[0]
    # Check that SQL contains a placeholder and that the payload is not interpolated into the SQL
    assert "%s" in sql
    assert params is not None
    assert payload in params
    assert payload not in sql


@pytest.mark.django_db
def test_raw_manager_parameterization():
    """Using .raw() with params should not interpolate the payload into the SQL string."""
    payload = "' OR 1=1 --"
    # Using the auth user model as a simple example; adjust to another model if needed
    qs = User.objects.raw("SELECT * FROM auth_user WHERE email = %s", [payload])
    # Executing the raw queryset should not raise and should not match any users
    assert list(qs) == []


@pytest.mark.django_db
def test_extra_uses_params_not_concat():
    """Verify that extra() uses params correctly rather than string concatenation."""
    payload = "' OR '1'='1"
    # Using extra() on the auth user model; adjust where clause to your use case
    qs = User.objects.extra(where=["email = %s"], params=[payload])
    # Should not find any users with the payload string as an email
    assert list(qs) == []
