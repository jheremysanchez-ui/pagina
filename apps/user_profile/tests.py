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
    # After deletion, get-review should return empty result or no review
    resp_after = api_client.get(f'/api/reviews/get-review/{product.id}')
    assert resp_after.status_code == 200
    # The response should not contain the deleted review
    assert resp_after.json().get('review') == {} or resp_after.json().get('review') is None
