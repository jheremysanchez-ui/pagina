"""
Tests for payment processing and token generation using mocks.

These tests validate that the payment endpoints integrate correctly with
Braintree by mocking the gateway.  Both successful and unsuccessful
payment scenarios are exercised, and the cart is verified to be
emptied on success.
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile
from apps.category.models import Category
from apps.product.models import Product
from apps.shipping.models import Shipping


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email='pay@example.com', password='Pay123!', first_name='Pay', last_name='User'):
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
    def _create_product(name='PayProd', price=20.0, compare_price=25.0, quantity=5, sold=0):
        category = Category.objects.create(name='PayCat')
        image = SimpleUploadedFile('pay.jpg', b'data', content_type='image/jpeg')
        return Product.objects.create(
            name=name,
            photo=image,
            description='Desc pay',
            price=price,
            compare_price=compare_price,
            category=category,
            quantity=quantity,
            sold=sold,
        )
    return _create_product


@patch('apps.payment.views.gateway.client_token.generate')
def test_generate_braintree_token(mock_generate, api_client):
    """Generating a Braintree token returns the mocked token."""
    mock_generate.return_value = 'mock_token'
    resp = api_client.get('/api/payment/get-token')
    assert resp.status_code == 200
    assert resp.json()['braintree_token'] == 'mock_token'


@patch('apps.payment.views.gateway.transaction.sale')
def test_successful_payment(mock_sale, api_client, create_user, create_product):
    """A successful payment creates an order and clears the cart."""
    # Mock Braintree sale success
    fake_result = MagicMock()
    fake_transaction = MagicMock()
    fake_transaction.id = 'sale123'
    fake_result.is_success = True
    fake_result.transaction = fake_transaction
    mock_sale.return_value = fake_result
    user = create_user(email='payok@example.com')
    api_client.force_authenticate(user=user)
    shipping = Shipping.objects.create(name='Pago Rápido', time_to_delivery='1 día', price='5.00')
    product = create_product()
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    payload = {
        'nonce': {'nonce': 'xyz'},
        'shipping_id': str(shipping.id),
        'coupon_name': '',
        'full_name': 'Pay User',
        'address_line_1': 'Dir 1',
        'address_line_2': '',
        'city': 'Ciudad',
        'state_province_region': 'Estado',
        'postal_zip_code': '000',
        'country_region': 'Ecuador',
        'telephone_number': '1111',
    }
    resp = api_client.post('/api/payment/make-payment', payload, format='json')
    assert resp.status_code == 200
    assert 'success' in resp.json()
    # Cart should be empty
    resp_cart = api_client.get('/api/cart/cart-items')
    assert resp_cart.status_code == 200
    assert resp_cart.json()['cart'] == []


@patch('apps.payment.views.gateway.transaction.sale')
def test_failed_payment(mock_sale, api_client, create_user, create_product):
    """A failed payment returns an error message and does not clear the cart."""
    fake_result = MagicMock()
    fake_result.is_success = False
    fake_result.transaction = None
    mock_sale.return_value = fake_result
    user = create_user(email='payfail@example.com')
    api_client.force_authenticate(user=user)
    shipping = Shipping.objects.create(name='Pago Lento', time_to_delivery='3 días', price='5.00')
    product = create_product()
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    payload = {
        'nonce': {'nonce': 'bad'},
        'shipping_id': str(shipping.id),
        'coupon_name': '',
        'full_name': 'Pay User',
        'address_line_1': 'Dir 1',
        'address_line_2': '',
        'city': 'Ciudad',
        'state_province_region': 'Estado',
        'postal_zip_code': '000',
        'country_region': 'Ecuador',
        'telephone_number': '1111',
    }
    resp = api_client.post('/api/payment/make-payment', payload, format='json')
    # Should return 400 or 200 with error depending on logic
    assert resp.status_code in (400, 200)
    assert 'error' in resp.json()
    # Cart should still have item
    resp_cart = api_client.get('/api/cart/cart-items')
    assert len(resp_cart.json()['cart']) == 1