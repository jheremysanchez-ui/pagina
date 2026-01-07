"""
CRUD tests for primary operations across various modules.

This module verifies that the API supports creating, retrieving,
updating and deleting resources via the endpoints exposed for carts,
wishlists and reviews.  It also exercises basic read operations for
orders.  Each test uses its own user and cleans up after itself.
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
from apps.orders.models import Order, OrderItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email='crud@example.com', password='Crud123!', first_name='Crud', last_name='User'):
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
    def _create_product(name='CRUD Product', price=20.0, compare_price=25.0, quantity=10, sold=0):
        category = Category.objects.create(name='CRUD Category')
        image = SimpleUploadedFile('crud.jpg', b'data', content_type='image/jpeg')
        return Product.objects.create(
            name=name,
            photo=image,
            description='Desc CRUD',
            price=price,
            compare_price=compare_price,
            category=category,
            quantity=quantity,
            sold=sold,
        )
    return _create_product


def test_cart_crud_flow(api_client, create_user, create_product):
    """Exercise create, read, update and delete operations on the cart."""
    user = create_user(email='cartcrud@example.com')
    api_client.force_authenticate(user=user)
    product = create_product()
    # Create (Add item)
    resp_add = api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    assert resp_add.status_code in (200, 201)
    # Read (Get items)
    resp_get = api_client.get('/api/cart/cart-items')
    assert resp_get.status_code == 200
    assert len(resp_get.json()['cart']) == 1
    # Update (Change quantity)
    resp_update = api_client.put('/api/cart/update-item', {'product_id': product.id, 'count': 3}, format='json')
    assert resp_update.status_code in (200, 202)
    # Delete (Remove item)
    resp_delete = api_client.delete('/api/cart/remove-item', {'product_id': product.id}, format='json')
    assert resp_delete.status_code == 200
    resp_after = api_client.get('/api/cart/cart-items')
    assert resp_after.status_code == 200
    assert resp_after.json()['cart'] == []


def test_wishlist_crud_flow(api_client, create_user, create_product):
    """Exercise create, read and delete operations on the wishlist."""
    user = create_user(email='wishlistcrud@example.com')
    api_client.force_authenticate(user=user)
    product = create_product()
    # Create (Add to wishlist)
    resp_add = api_client.post('/api/wishlist/add-item', {'product_id': product.id}, format='json')
    assert resp_add.status_code == 201
    # Read (Get items)
    resp_get = api_client.get('/api/wishlist/wishlist-items')
    assert resp_get.status_code == 200
    assert len(resp_get.json()['wishlist']) == 1
    # Delete (Remove)
    resp_delete = api_client.delete('/api/wishlist/remove-item', {'product_id': product.id}, format='json')
    assert resp_delete.status_code == 200
    resp_after = api_client.get('/api/wishlist/wishlist-items')
    assert resp_after.json()['wishlist'] == []


def test_review_crud_flow(api_client, create_user, create_product):
    """Exercise create, read, update and delete operations on reviews."""
    user = create_user(email='reviewcrud@example.com')
    api_client.force_authenticate(user=user)
    product = create_product()
    # Create review
    resp_create = api_client.post(
        f'/api/reviews/create-review/{product.id}',
        {'rating': 4.0, 'comment': 'Muy bueno'},
        format='json',
    )
    assert resp_create.status_code == 201
    # Read review
    resp_get = api_client.get(f'/api/reviews/get-review/{product.id}')
    assert resp_get.status_code == 200
    assert resp_get.json()['review']['rating'] == 4.0
    # Update review
    resp_update = api_client.put(
        f'/api/reviews/update-review/{product.id}',
        {'rating': 3.0, 'comment': 'Mejorable'},
        format='json',
    )
    assert resp_update.status_code == 200
    assert resp_update.json()['review']['rating'] == 3.0
    # Delete review
    resp_delete = api_client.delete(f'/api/reviews/delete-review/{product.id}')
    assert resp_delete.status_code == 200
    # Ensure review gone
    resp_get_after = api_client.get(f'/api/reviews/get-review/{product.id}')
    assert resp_get_after.status_code == 200
    assert resp_get_after.json()['review'] == {}


def test_order_read_operations(api_client, create_user):
    """Create an order directly and verify list and detail endpoints."""
    user = create_user(email='ordercrud@example.com')
    api_client.force_authenticate(user=user)
    # Create dummy order and order item
    order = Order.objects.create(
        user=user,
        transaction_id='crudtxn',
        amount='50.00',
        full_name='CRUD User',
        address_line_1='Main',
        address_line_2='',
        city='City',
        state_province_region='State',
        postal_zip_code='123',
        country_region='Ecuador',
        telephone_number='123',
        shipping_name='Standard',
        shipping_time='3-5 días',
        shipping_price='5.00',
    )
    OrderItem.objects.create(order=order, product=None, name='Item', price='25.00', count=2)
    # Read list
    resp_list = api_client.get('/api/orders/get-orders')
    assert resp_list.status_code == 200
    assert any(o['transaction_id'] == 'crudtxn' for o in resp_list.json()['orders'])
    # Read detail
    resp_detail = api_client.get(f'/api/orders/get-order/{order.transaction_id}')
    assert resp_detail.status_code == 200
    assert resp_detail.json()['order']['transaction_id'] == 'crudtxn'