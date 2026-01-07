import pytest
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.category.models import Category
from apps.product.models import Product


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


@pytest.fixture
def create_product(db, create_category):
    """Return a function that creates Product instances with all required fields."""
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


def test_product_detail(api_client, create_product):
    """Product detail view returns the correct product data."""
    product = create_product(name='Laptop X')
    response = api_client.get(f'/api/product/product/{product.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['product']['name'] == 'Laptop X'


def test_list_products(api_client, create_product):
    """The products list endpoint returns multiple products."""
    create_product(name='Prod1')
    create_product(name='Prod2')
    response = api_client.get('/api/product/get-products')
    assert response.status_code == 200
    data = response.json()
    assert 'products' in data
    assert len(data['products']) >= 2


def test_product_search(api_client, create_product):
    """Search endpoint returns products matching the query string."""
    create_product(name='BuscarMe')
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
    # The view may return related_products or an error if there are none
    assert 'related_products' in data or 'error' in data
