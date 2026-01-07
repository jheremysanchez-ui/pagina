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
    return APIClient()


@pytest.fixture
def create_user(db):
    """Return a function to create a user with required related objects."""
    def _create_user(email='user@example.com', password='Password123!', first_name='Test', last_name='User'):
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


def test_wishlist_operations(api_client, create_user, create_product):
    """Add, list and remove wishlist items returns correct state."""
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
    resp_remove = api_client.delete('/api/wishlist/remove-item', {'product_id': product.id})
    assert resp_remove.status_code == 200
    # After removal, wishlist should be empty
    resp_after = api_client.get('/api/wishlist/wishlist-items')
    assert resp_after.status_code == 200
    assert resp_after.json()['wishlist'] == []
