import pytest
from rest_framework.test import APIClient

from apps.shipping.models import Shipping


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


def test_shipping_options(api_client, db):
    """Shipping options endpoint returns available shipping methods."""
    Shipping.objects.create(name='Standard', time_to_delivery='5-7 días', price='10.00')
    Shipping.objects.create(name='Express', time_to_delivery='1-2 días', price='20.00')
    response = api_client.get('/api/shipping/get-shipping-options')
    assert response.status_code == 200
    data = response.json()
    assert 'shipping_options' in data
    assert len(data['shipping_options']) == 2
