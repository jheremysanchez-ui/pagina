"""
Tests to validate business rules such as stock levels, totals and
logical state transitions.  These tests ensure that error messages
appear when trying to exceed available stock and that totals are
calculated correctly.
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
from apps.shipping.models import Shipping
from apps.coupons.models import FixedPriceCoupon


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email='rules@example.com', password='Rules123!', first_name='Rules', last_name='User'):
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


@pytest.fixture
def create_product(db):
    def _create_product(name='Rule Prod', price=30.0, compare_price=40.0, quantity=3, sold=0):
        category = Category.objects.create(name='RulesCat')
        image = SimpleUploadedFile('rules.jpg', b'data', content_type='image/jpeg')
        return Product.objects.create(
            name=name,
            photo=image,
            description='Desc rules',
            price=price,
            compare_price=compare_price,
            category=category,
            quantity=quantity,
            sold=sold,
        )
    return _create_product


def test_cannot_add_more_than_stock(api_client, create_user, create_product):
    """Adding more items than available stock results in an error response."""
    user = create_user(email='stock@example.com')
    api_client.force_authenticate(user=user)
    product = create_product(quantity=1)
    # Add one item to cart
    response = api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    assert response.status_code in [200, 201]
    # Attempt to update count beyond stock
    resp = api_client.put(
        '/api/cart/update-item',
        {'product_id': product.id, 'count': 2},
        format='json',
    )
    # Should return 200 with error message in body
    assert resp.status_code == 200
    assert 'error' in resp.json()


def test_payment_total_requires_items(api_client, create_user, create_product):
    """Requesting payment totals with an empty cart returns an error."""
    user = create_user(email='noprod@example.com')
    api_client.force_authenticate(user=user)
    # No items in cart
    resp = api_client.get('/api/payment/get-payment-total', {'shipping_id': '', 'coupon_name': ''})
    # Should indicate need items
    assert resp.status_code == 404
    assert 'error' in resp.json()


def test_payment_total_insufficient_stock(api_client, create_user, create_product):
    """Payment total should error if cart contains more than available stock."""
    user = create_user(email='lowstock@example.com')
    api_client.force_authenticate(user=user)
    product = create_product(quantity=1)
    # Add item to cart
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Update count to exceed stock
    api_client.put(
        '/api/cart/update-item',
        {'product_id': product.id, 'count': 2},
        format='json',
    )
    # Attempt to get payment total; expect 200 with error message
    resp = api_client.get('/api/payment/get-payment-total', {'shipping_id': '', 'coupon_name': ''})
    assert resp.status_code == 200
    assert 'error' in resp.json()


def test_invalid_shipping_in_payment(api_client, create_user, create_product):
    """Processing payment with invalid shipping id yields a 404 error."""
    user = create_user(email='invalidship@example.com')
    api_client.force_authenticate(user=user)
    product = create_product()
    # Add item to cart
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    payload = {
        'nonce': {'nonce': 'bad'},
        'shipping_id': '999',  # non‑existent
        'coupon_name': '',
        'full_name': 'Invalid Ship',
        'address_line_1': 'Street',
        'address_line_2': '',
        'city': 'City',
        'state_province_region': 'State',
        'postal_zip_code': '123',
        'country_region': 'Ecuador',
        'telephone_number': '123456',
    }
    resp = api_client.post('/api/payment/make-payment', payload, format='json')
    assert resp.status_code == 404
    assert 'error' in resp.json()