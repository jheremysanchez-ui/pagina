import pytest
from rest_framework.test import APIClient
from apps.category.models import Category


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def create_category(db):
    """Return a function that creates Category instances."""
    def _create_category(name='Category', parent=None):
        return Category.objects.create(name=name, parent=parent)
    return _create_category


def test_list_categories(api_client, create_category):
    """Listing categories returns parent and child categories."""
    parent = create_category(name='Electrónica')
    create_category(name='Computadoras', parent=parent)
    response = api_client.get('/api/category/categories')
    assert response.status_code == 200
    data = response.json()
    assert 'categories' in data
    names = [c['name'] for c in data['categories']]
    assert 'Electrónica' in names
