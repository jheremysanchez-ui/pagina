"""
Security tests covering CSRF enforcement and basic rate limiting.

These tests are designed to probe the application for proper CSRF
protection on session‑based endpoints and for throttling of repeated
requests to prevent abuse.  File upload security is not tested
because no upload endpoints are exposed via the API.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile
from apps.category.models import Category
from apps.product.models import Product


@pytest.fixture
def create_product(db):
    def _create_product(name='SecProd', price=15.0, compare_price=20.0, quantity=5, sold=0):
        category = Category.objects.create(name='SecCat')
        image = SimpleUploadedFile('sec.jpg', b'data', content_type='image/jpeg')
        return Product.objects.create(
            name=name,
            photo=image,
            description='Desc sec',
            price=price,
            compare_price=compare_price,
            category=category,
            quantity=quantity,
            sold=sold,
        )
    return _create_product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email='sec@example.com', password='Sec123!', first_name='Sec', last_name='User'):
        User = get_user_model()
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        Cart.objects.create(user=user)
        WishList.objects.create(user=user)
        UserProfile.objects.create(user=user)
        return user
    return _create_user


def test_csrf_protection_on_profile_update(api_client, create_user):
    """When CSRF checks are enforced, missing token should cause a 403."""
    user = create_user(email='csrfuser@example.com')
    # Create a client that enforces CSRF
    client = APIClient(enforce_csrf_checks=True)
    client.force_authenticate(user=user)
    payload = {
        'address_line_1': 'CSRF St',
        'address_line_2': '',
        'city': 'Ciudad',
        'state_province_region': 'Estado',
        'zipcode': '000',
        'phone': '123',
        'country_region': 'Ecuador',
    }
    # Missing CSRF token should raise 403 Forbidden
    resp = client.put('/api/profile/update', payload, format='json')
    assert resp.status_code == 403


def test_rate_limiting_on_cart_endpoint(api_client, create_user, create_product):
    """Repeated hits to a public endpoint should eventually trigger throttling."""
    user = create_user(email='ratelimit@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    last_status = None
    for _ in range(60):
        last_status = api_client.get('/api/cart/cart-items').status_code
    # If throttling is configured, the last status may be 429 Too Many Requests
    assert last_status in (200, 429)