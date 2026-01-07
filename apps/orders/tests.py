import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.orders.models import Order, OrderItem


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Return a function that creates a user."""
    def _create_user(email='user@example.com', password='Password123!', first_name='Test', last_name='User'):
        User = get_user_model()
        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
    return _create_user


def test_orders_list_and_detail(api_client, create_user):
    """Listing orders and retrieving order details returns the created order."""
    user = create_user(email='orders@example.com')
    api_client.force_authenticate(user=user)
    # Create an order directly
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
    # Add at least one order item so the detail view includes items
    OrderItem.objects.create(
        product=None,
        order=order,
        name='ItemName',
        price='20.00',
        count=1,
    )
    # List orders
    resp_list = api_client.get('/api/orders/get-orders')
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    assert 'orders' in data_list
    assert any(o['transaction_id'] == 'txn1234' for o in data_list['orders'])
    # Detail order
    resp_detail = api_client.get(f'/api/orders/get-order/{order.transaction_id}')
    assert resp_detail.status_code == 200
    data_detail = resp_detail.json()
    assert data_detail['order']['transaction_id'] == 'txn1234'
