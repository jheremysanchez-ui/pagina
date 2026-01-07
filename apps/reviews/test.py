import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.cart.models import Cart
from apps.wishlist.models import WishList
from apps.user_profile.models import UserProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    """Return a function that creates a user and attaches cart, wishlist and profile."""
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


def test_user_profile_get_and_update(api_client, create_user):
    """User profile retrieval and update endpoints return and save profile data."""
    user = create_user(email='profile@example.com')
    api_client.force_authenticate(user=user)
    # Initial get
    resp_get = api_client.get('/api/profile/user')
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert 'profile' in data
    # Default address_line_1 should be empty string
    assert data['profile']['address_line_1'] == ''
    # Update profile
    update_data = {
        'address_line_1': 'Av 1',
        'address_line_2': 'Edificio 2',
        'city': 'Cuenca',
        'state_province_region': 'Azuay',
        'zipcode': '010101',
        'phone': '0999999999',
        'country_region': 'Ecuador',
    }
    resp_update = api_client.put('/api/profile/update', update_data, format='json')
    assert resp_update.status_code == 200
    updated_profile = resp_update.json()['profile']
    assert updated_profile['address_line_1'] == 'Av 1'
    assert updated_profile['city'] == 'Cuenca'
