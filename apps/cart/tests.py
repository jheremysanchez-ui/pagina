import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.category.models import Category
from apps.product.models import Product
from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Return a function that creates a user and associated cart, wishlist and profile."""
    def _create_user(email='user@example.com', password='Password123!', first_name='Test', last_name='User'):
        User = get_user_model()
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        # Create one‑to‑one related objects required by the cart and wishlist apps
        Cart.objects.create(user=user)
        WishList.objects.create(user=user)
        UserProfile.objects.create(user=user)
        return user
    return _create_user


@pytest.fixture
def create_category(db):
    """Return a function that creates Category instances."""
    def _create_category(name='Category', parent=None):
        return Category.objects.create(name=name, parent=parent)
    return _create_category


@pytest.fixture
def create_product(db, create_category):
    """Return a function that creates Product instances with required fields."""
    def _create_product(
        name='Product', price=10.0, compare_price=15.0, quantity=10, sold=0,
        category=None
    ):
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


def test_cart_add_and_get(api_client, create_user, create_product):
    """Adding an item to the cart and retrieving it returns the correct contents."""
    user = create_user(email='cartuser@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add an item to the cart
    resp_add = api_client.post(
        '/api/cart/add-item',
        {'product_id': product.id},
        format='json',
    )
    assert resp_add.status_code in (200, 201)
    # Retrieve cart items
    resp_get = api_client.get('/api/cart/cart-items')
    assert resp_get.status_code == 200
    cart_data = resp_get.json()
    assert 'cart' in cart_data
    assert any(item['product']['id'] == product.id for item in cart_data['cart'])


def test_cart_total_and_item_total(api_client, create_user, create_product):
    """Cart total cost and total items reflect added products."""
    user = create_user(email='carttotals@example.com')
    product = create_product(price=50.0, compare_price=60.0)
    api_client.force_authenticate(user=user)
    # Add an item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Get total cost
    resp_total = api_client.get('/api/cart/get-total')
    assert resp_total.status_code == 200
    data_total = resp_total.json()
    assert float(data_total['total_cost']) == 50.0
    # Get total items
    resp_items = api_client.get('/api/cart/get-item-total')
    assert resp_items.status_code == 200
    assert int(resp_items.json()['total_items']) >= 1


def test_cart_update_and_remove_item(api_client, create_user, create_product):
    """Updating the quantity and removing an item updates the cart contents."""
    user = create_user(email='cartupdate@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Update quantity (count=2)
    resp_update = api_client.put(
        '/api/cart/update-item',
        {'product_id': product.id, 'count': 2},
        format='json',
    )
    assert resp_update.status_code in (200, 202)
    # Remove item
    resp_remove = api_client.delete(
        '/api/cart/remove-item',
        {'product_id': product.id},
    )
    assert resp_remove.status_code == 200
    # Verify cart is empty
    resp_final = api_client.get('/api/cart/cart-items')
    assert resp_final.status_code == 200
    assert len(resp_final.json()['cart']) == 0


def test_cart_empty(api_client, create_user, create_product):
    """Emptying the cart clears all items from the cart."""
    user = create_user(email='emptycart@example.com')
    product = create_product()
    api_client.force_authenticate(user=user)
    # Add item
    api_client.post('/api/cart/add-item', {'product_id': product.id}, format='json')
    # Empty the cart
    resp_empty = api_client.delete('/api/cart/empty')
    assert resp_empty.status_code == 200
    # Ensure cart is empty
    resp_final = api_client.get('/api/cart/cart-items')
    assert resp_final.status_code == 200
    assert len(resp_final.json()['cart']) == 0
