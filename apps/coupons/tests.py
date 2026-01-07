import pytest
from rest_framework.test import APIClient

from apps.coupons.models import FixedPriceCoupon, PercentageCoupon


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


def test_check_coupon_valid_and_invalid(api_client, db):
    """Coupon endpoint validates existing coupons and rejects invalid ones."""
    FixedPriceCoupon.objects.create(name='DESC10', discount_price='10.00')
    # Valid coupon
    resp_valid = api_client.get('/api/coupons/check-coupon', {'coupon_name': 'DESC10'})
    assert resp_valid.status_code == 200
    data = resp_valid.json()
    assert 'coupon' in data
    assert data['coupon']['name'] == 'DESC10'
    # Invalid coupon returns 404
    resp_invalid = api_client.get('/api/coupons/check-coupon', {'coupon_name': 'INVALID'})
    assert resp_invalid.status_code == 404
