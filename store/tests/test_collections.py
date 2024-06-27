from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
import pytest
from model_bakery import baker
from store.models import Collection, Product


@pytest.mark.django_db
class TestCreateCollection:

    # @pytest.mark.django_db
    # @pytest.mark.skip
    def test_if_user_anonymous_returns_404(self, api_client):
        # arrange

        # act
        response = api_client.post("/store/collections/", {"title": "A"})
        # assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_is_user_not_admin_returns_403(self, api_client):
        api_client.force_authenticate(user={})
        response = api_client.post("/store/collections/", {"title": "A"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_data_is_invalid_returns_400(self, api_client):
        api_client.force_authenticate(user=User(is_staff=True))
        response = api_client.post("/store/collections/", {"title": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['title'] is not None

    def test_if_data_is_invalid_returns_201(self, api_client):
        api_client.force_authenticate(user=User(is_staff=True))
        response = api_client.post("/store/collections/", {"title": "A"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0


@pytest.mark.django_db
class TestRetrieveCollection:
    def test_collection_if_exists_returns_200(self, api_client):
        collection = baker.make(Collection)

        # Default All the collection will be diff
        # product = baker.make(Product, collection=collection, _quantity=10)

        response = api_client.get(f'/store/collections/{collection.id}/')
        assert response.status_code == status.HTTP_200_OK
        # assert response.data['id'] == collection.id
        assert response.data == {
            "id" : collection.id,
            "title" : collection.title,
            "products_count": 0
        }
