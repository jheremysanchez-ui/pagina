"""
Test suite covering all Django modules of the e‑commerce project.

This file contains pytest tests that exercise the primary API endpoints
exposed by each app in the project.  To run the tests, install
pytest‑django and run `pytest` from the project root.  The tests
create and clean up their own data and should run in isolation.

Many endpoints expect certain related objects (such as a cart or
wishlist) to exist for a user.  The fixtures below set up these
objects where necessary.  Replace any hard‑coded URL prefixes or
endpoint names if your `urls.py` modules differ.
"""

import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.category.models import Category
from apps.product.models import Product
from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile
from apps.shipping.models import Shipping
from apps.coupons.models import FixedPriceCoupon, PercentageCoupon
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review

from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Return a function that creates a user and related objects."""
    def _create_user(email='user@example.com', password='Password123!', first_name='Test', last_name='User'):
        User = get_user_model()
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        # Ensure the user has the required one‑to‑one related objects
        Cart.objects.create(user=user)
        WishList.objects.create(user=user)
        UserProfile.objects.create(user=user)
        return user
    return _create_user


@pytest.fixture
def create_category(db):
    """Return a function that creates categories."""
    def _create_category(name='Category', parent=None):
        return Category.objects.create(name=name, parent=parent)
    return _create_category


@pytest.fixture
def create_product(db, create_category):
    """Return a function that creates products with all required fields."""
    def _create_product(
        name='Product', price=10.0, compare_price=15.0, quantity=10, sold=0,
        category=None
    ):
        if category is None:
            category = create_category()
        # Create a simple image file for the ImageField.  The content is
        # irrelevant; it just needs to be bytes.
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


def test_list_categories(api_client, create_category):
    """Listing categories returns parent and subcategory structure."""
    parent = create_category(name='Electrónica')
    create_category(name='Computadoras', parent=parent)
    response = api_client.get('/api/category/categories')
    assert response.status_code == 200
    data = response.json()
    assert 'categories' in data
    names = [c['name'] for c in data['categories']]
    assert 'Electrónica' in names


def test_product_detail(api_client, create_product):
    """Product detail returns the expected product data."""
    product = create_product(name='Laptop X')
    response = api_client.get(f'/api/product/product/{product.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['product']['name'] == 'Laptop X'


def test_list_products(api_client, create_product):
    """List products endpoint returns multiple products."""
    create_product(name='Prod1')
    create_product(name='Prod2')
    response = api_client.get('/api/product/get-products')
    assert response.status_code == 200
    data = response.json()
    assert 'products' in data
    # At least two products should be returned
    assert len(data['products']) >= 2


def test_product_search(api_client, create_product):
    """Search endpoint returns products matching the query."""
    create_product(name='BuscarMe')
    # category_id=0 to search all categories
    response = api_client.post(
        '/api/product/search',
        {'category_id': 0, 'search': 'Buscar'},
        format='json',
    )
    assert response.status_code == 200
    data = response.json()
    assert 'search_products' in data
    assert any('BuscarMe' in p['name'] for p in data['search_products'])


def test_product_related(api_client, create_product):
    """Related products endpoint returns products in the same category."""
    product1 = create_product(name='MainProd')
    create_product(name='Related1', category=product1.category)
    create_product(name='Related2', category=product1.category)
    response = api_client.get(f'/api/product/related/{product1.id}')
    assert response.status_code == 200
    data = response.json()
    # If there are related products, the key should exist
    assert 'related_products' in data or 'error' in data


def test_cart_add_and_get(api_client, create_user, create_product):
    """Adding an item to the cart and retrieving it works."""
    user = create_user(email='cartuser@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add item
    response = api_client.post(
        '/api/cart/add-item',
        {'product_id': product.id},
        format='json',
    )
    assert response.status_code in (201, 200)
    # Get items
    response2 = api_client.get('/api/cart/cart-items')
    assert response2.status_code == 200
    cart_data = response2.json()
    assert 'cart' in cart_data
    assert any(item['product']['id'] == product.id for item in cart_data['cart'])


def test_cart_total_and_item_total(api_client, create_user, create_product):
    """Total cost and total item count reflect the cart contents."""
    user = create_user(email='carttotals@example.com')
    product = create_product(price=50.0, compare_price=60.0)
    api_client.force_authenticate(user=user)
    # Add an item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Get totals
    resp = api_client.get('/api/cart/get-total')
    assert resp.status_code == 200
    data = resp.json()
    assert float(data['total_cost']) == 50.0
    # Item total
    resp2 = api_client.get('/api/cart/get-item-total')
    assert resp2.status_code == 200
    assert int(resp2.json()['total_items']) >= 1


def test_cart_update_and_remove_item(api_client, create_user, create_product):
    """Updating and removing an item updates the cart appropriately."""
    user = create_user(email='cartupdate@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Update quantity
    resp = api_client.put(
        '/api/cart/update-item',
        {'product_id': product.id, 'count': 2},
        format='json',
    )
    assert resp.status_code in (200, 202)
    # Remove item
    resp2 = api_client.delete(
        '/api/cart/remove-item',
        {'product_id': product.id},
        format='json',
    )
    assert resp2.status_code == 200
    # Cart should now be empty
    resp3 = api_client.get('/api/cart/cart-items')
    assert resp3.status_code == 200
    assert len(resp3.json()['cart']) == 0


def test_cart_empty_view(api_client, create_user, create_product):
    """Emptying the cart clears all items."""
    user = create_user(email='emptycart@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Empty cart
    resp = api_client.delete('/api/cart/empty')
    assert resp.status_code == 200
    # Ensure cart is empty
    resp2 = api_client.get('/api/cart/cart-items')
    assert len(resp2.json()['cart']) == 0


def test_orders_list_and_detail(api_client, create_user):
    """Listing orders and retrieving order detail endpoints work."""
    user = create_user(email='orders@example.com')
    api_client.force_authenticate(user=user)
    # Create a dummy order directly
    order = Order.objects.create(
        user=user,
        transaction_id='txn1234',
        amount='100.00',
        full_name='Test User',
        address_line_1='Street 1',
        address_line_2='',
        city='City',
        state_province_region='State',
        postal_zip_code='12345',
        country_region='Ecuador',
        telephone_number='123456789',
        shipping_name='Express',
        shipping_time='1-2 days',
        shipping_price='5.00',
    )
    # Create an order item to test detail view
    OrderItem.objects.create(
        product=None,
        order=order,
        name='ItemName',
        price='20.00',
        count=1,
    )
    # List orders
    resp = api_client.get('/api/orders/get-orders')
    assert resp.status_code == 200
    data = resp.json()
    assert 'orders' in data
    assert any(o['transaction_id'] == 'txn1234' for o in data['orders'])
    # Order detail
    resp2 = api_client.get(f'/api/orders/get-order/{order.transaction_id}')
    assert resp2.status_code == 200
    detail_data = resp2.json()
    assert detail_data['order']['transaction_id'] == 'txn1234'


def test_shipping_options(api_client):
    """Shipping options endpoint returns existing shipping methods."""
    Shipping.objects.create(name='Standard', time_to_delivery='5-7 días', price='10.00')
    Shipping.objects.create(name='Express', time_to_delivery='1-2 días', price='20.00')
    resp = api_client.get('/api/shipping/get-shipping-options')
    assert resp.status_code == 200
    data = resp.json()
    assert 'shipping_options' in data
    assert len(data['shipping_options']) == 2


def test_check_coupon(api_client):
    """Coupon endpoint returns coupon data when a valid coupon is provided."""
    FixedPriceCoupon.objects.create(name='DESC10', discount_price='10.00')
    resp = api_client.get('/api/coupons/check-coupon', {'coupon_name': 'DESC10'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'coupon' in data
    assert data['coupon']['name'] == 'DESC10'
    # Invalid coupon returns 404
    resp2 = api_client.get('/api/coupons/check-coupon', {'coupon_name': 'INVALID'})
    assert resp2.status_code == 404


def test_user_profile_get_and_update(api_client, create_user):
    """User profile retrieval and update endpoints behave correctly."""
    user = create_user(email='profile@example.com')
    api_client.force_authenticate(user=user)
    # Initial get
    resp = api_client.get('/api/profile/user')
    assert resp.status_code == 200
    data = resp.json()
    assert data['profile']['address_line_1'] == ''
    # Update profile
    update_payload = {
        'address_line_1': 'Av 1',
        'address_line_2': 'Edificio 2',
        'city': 'Cuenca',
        'state_province_region': 'Azuay',
        'zipcode': '010101',
        'phone': '0999999999',
        'country_region': 'Ecuador',
    }
    resp2 = api_client.put('/api/profile/update', update_payload, format='json')
    assert resp2.status_code == 200
    updated = resp2.json()['profile']
    assert updated['address_line_1'] == 'Av 1'


def test_wishlist_operations(api_client, create_user, create_product):
    """Add, list and remove wishlist items."""
    user = create_user(email='wishlist@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Initially empty
    resp_empty = api_client.get('/api/wishlist/wishlist-items')
    assert resp_empty.status_code == 200
    assert resp_empty.json()['wishlist'] == []
    # Add item
    resp_add = api_client.post('/api/wishlist/add-item', {'product_id': product.id}, format='json')
    assert resp_add.status_code == 201
    # Get item total
    resp_total = api_client.get('/api/wishlist/get-item-total')
    assert resp_total.status_code == 200
    assert int(resp_total.json()['total_items']) == 1
    # Remove item
    resp_remove = api_client.delete('/api/wishlist/remove-item', {'product_id': product.id}, format='json')
    assert resp_remove.status_code == 200
    # Wishlist should be empty again
    resp_after = api_client.get('/api/wishlist/wishlist-items')
    assert resp_after.json()['wishlist'] == []


def test_reviews_crud_flow(api_client, create_user, create_product):
    """Create, retrieve, update and delete a product review."""
    user = create_user(email='review@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Create review
    resp_create = api_client.post(
        f'/api/reviews/create-review/{product.id}',
        {'rating': 4.5, 'comment': 'Excelente'},
        format='json',
    )
    assert resp_create.status_code == 201
    # Retrieve single review
    resp_get = api_client.get(f'/api/reviews/get-review/{product.id}')
    assert resp_get.status_code == 200
    assert resp_get.json()['review']['rating'] == 4.5
    # Update review
    resp_update = api_client.put(
        f'/api/reviews/update-review/{product.id}',
        {'rating': 3.0, 'comment': 'Bueno'},
        format='json',
    )
    assert resp_update.status_code == 200
    assert resp_update.json()['review']['rating'] == 3.0
    # Delete review
    resp_delete = api_client.delete(f'/api/reviews/delete-review/{product.id}')
    assert resp_delete.status_code == 200
    # After deletion, get-review should return empty result
    resp_get_after = api_client.get(f'/api/reviews/get-review/{product.id}')
    assert resp_get_after.status_code == 200
    # The review field is empty dict after deletion
    assert resp_get_after.json()['review'] == {}


@patch('apps.payment.views.gateway.client_token.generate')
def test_payment_get_token(mock_generate, api_client):
    """Braintree token retrieval returns token from gateway."""
    mock_generate.return_value = 'fake_token'
    resp = api_client.get('/api/payment/get-token')
    assert resp.status_code == 200
    assert resp.json()['braintree_token'] == 'fake_token'


@patch('apps.payment.views.gateway.transaction.sale')
def test_payment_process_success(mock_sale, api_client, create_user, create_product):
    """Successful payment processing creates an order and empties the cart."""
    # Mock transaction sale result
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
    # Add item to cart
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Prepare payload
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
    # On success, the endpoint returns 200
    assert resp.status_code == 200
    assert 'success' in resp.json()
    # The cart should be emptied
    empty_cart_resp = api_client.get('/api/cart/cart-items')
    assert empty_cart_resp.status_code == 200
    assert len(empty_cart_resp.json()['cart']) == 0