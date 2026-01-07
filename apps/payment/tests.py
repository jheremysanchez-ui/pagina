import pytest
from unittest.mock import patch, MagicMock

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.category.models import Category
from apps.product.models import Product
from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile
from apps.shipping.models import Shipping


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email='user@example.com', password='Password123!', first_name='Test', last_name='User'):
        User = get_user_model()
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        # Attach related objects for cart and wishlist
        Cart.objects.create(user=user)
        WishList.objects.create(user=user)
        UserProfile.objects.create(user=user)
        return user
    return _create_user


@pytest.fixture
def create_category(db):
    def _create_category(name='Category', parent=None):
        return Category.objects.create(name=name, parent=parent)
    return _create_category


@pytest.fixture
def create_product(db, create_category):
    def _create_product(name='Product', price=10.0, compare_price=15.0, quantity=10, sold=0, category=None):
        if category is None:
            category = create_category()
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'smallcontent',
            content_type='image/jpeg',
        )
        return Product.objects.create(
            name=name,
            photo=image,
            description='Descripción de prueba',
            price=price,
            compare_price=compare_price,
            category=category,
            quantity=quantity,
            sold=sold,
        )
    return _create_product


@patch('apps.payment.views.gateway.client_token.generate')
def test_payment_get_token(mock_generate, api_client):
    """Braintree token endpoint returns a token from the gateway."""
    mock_generate.return_value = 'fake_token'
    resp = api_client.get('/api/payment/get-token')
    assert resp.status_code == 200
    assert resp.json()['braintree_token'] == 'fake_token'


@patch('apps.payment.views.gateway.transaction.sale')
def test_payment_process_success(mock_sale, api_client, create_user, create_product):
    """Successful payment processing empties the cart and returns success."""
    # Mock successful transaction
    fake_result = MagicMock()
    fake_transaction = MagicMock()
    fake_transaction.id = 'tran123'
    fake_result.is_success = True
    fake_result.transaction = fake_transaction
    mock_sale.return_value = fake_result

    user = create_user(email='payment@example.com')
    api_client.force_authenticate(user=user)
    # Create shipping option and product
    shipping = Shipping.objects.create(name='Rápido', time_to_delivery='2 días', price='5.00')
    product = create_product(price=30.0, compare_price=35.0)
    # Add an item to the cart
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Prepare payment payload
    payload = {
        'nonce': {'nonce': 'dummy_nonce'},
        'shipping_id': str(shipping.id),
        'coupon_name': '',
        'full_name': 'Pagador',
        'address_line_1': 'Calle 1',
        'address_line_2': '',
        'city': 'Ambato',
        'state_province_region': 'Tungurahua',
        'postal_zip_code': '180101',
        'country_region': 'Ecuador',
        'telephone_number': '0987654321',
    }
    resp = api_client.post('/api/payment/make-payment', payload, format='json')
    assert resp.status_code == 200
    data = resp.json()
    assert 'success' in data
    # Ensure cart is empty after successful payment
    resp_cart = api_client.get('/api/cart/cart-items')
    assert resp_cart.status_code == 200
    assert len(resp_cart.json()['cart']) == 0
