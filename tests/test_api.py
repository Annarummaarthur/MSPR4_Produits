# tests/test_api.py
from unittest.mock import patch


class TestProductAPI:
    """Test suite for Product API endpoints"""

    def test_read_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API is running"}

    def test_protected_route_without_token(self, client):
        """Test accessing protected route without authentication"""
        response = client.get("/products")
        assert response.status_code == 403

    def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/products", headers=headers)
        assert response.status_code == 403

    def test_create_product_without_auth(self, client, sample_product_data):
        """Test creating product without authentication should fail"""
        response = client.post("/products", json=sample_product_data)
        assert response.status_code == 403

    def test_create_product_minimal_data(self, client, auth_headers):
        """Test creating product with minimal required data"""
        minimal_data = {"name": "Produit Minimal", "price": 10.0}
        response = client.post("/products", json=minimal_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Produit Minimal"
        assert data["price"] == 10.0

    def test_create_product_invalid_data(self, client, auth_headers):
        """Test creating product with invalid data"""
        invalid_data = {"description": "Description sans nom ni prix"}
        response = client.post("/products", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_list_products(self, client, auth_headers):
        """Test listing all products"""
        products_data = [
            {"name": "Produit 1", "price": 10.0},
            {"name": "Produit 2", "price": 20.0},
            {"name": "Produit 3", "price": 30.0},
        ]

        created_products = []
        for data in products_data:
            response = client.post("/products", json=data, headers=auth_headers)
            assert response.status_code == 200
            created_products.append(response.json())

        response = client.get("/products", headers=auth_headers)
        assert response.status_code == 200

        products_list = response.json()
        assert isinstance(products_list, list)
        assert len(products_list) >= len(products_data)

    def test_get_nonexistent_product(self, client, auth_headers):
        """Test getting non-existent product should return 404"""
        response = client.get("/products/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_product(self, client, auth_headers, created_product):
        """Test updating product data"""
        product_id = created_product["id"]

        update_data = {
            "name": "Produit Modifié",
            "price": 25.99,
            "description": "Description modifiée",
        }

        response = client.put(
            f"/products/{product_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200

        updated_product = response.json()
        assert updated_product["name"] == "Produit Modifié"
        assert updated_product["price"] == 25.99
        assert updated_product["description"] == "Description modifiée"

    def test_update_nonexistent_product(self, client, auth_headers):
        """Test updating non-existent product should return 404"""
        update_data = {"name": "Produit Inexistant"}
        response = client.put("/products/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_product(self, client, auth_headers, created_product):
        """Test deleting a product"""
        product_id = created_product["id"]

        response = client.delete(f"/products/{product_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "Produit supprimé avec succès" in response.json()["message"]

        get_response = client.get(f"/products/{product_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_product(self, client, auth_headers):
        """Test deleting non-existent product should return 404"""
        response = client.delete("/products/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_create_product_zero_price(self, client, auth_headers):
        """Test creating product with zero price"""
        data = {"name": "Produit Gratuit", "price": 0.0}
        response = client.post("/products", json=data, headers=auth_headers)
        assert response.status_code in [200, 422]

    def test_create_product_large_price(self, client, auth_headers):
        """Test creating product with very large price"""
        data = {"name": "Produit Cher", "price": 999999.99}
        response = client.post("/products", json=data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["price"] == 999999.99

    def test_create_product_special_characters(self, client, auth_headers):
        """Test creating product with special characters in name"""
        data = {
            "name": "Café & Thé François",
            "price": 15.50,
            "description": "Café spécialisé français",
        }
        response = client.post("/products", json=data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Café & Thé François"

    def test_create_product_negative_stock(self, client, auth_headers):
        """Test creating product with negative stock"""
        data = {"name": "Produit Stock Négatif", "price": 10.0, "stock": -5}
        response = client.post("/products", json=data, headers=auth_headers)
        assert response.status_code in [200, 422]

    def test_price_formatting(self, client, auth_headers):
        """Test price formatting and precision"""
        data = {"name": "Produit Prix Précis", "price": 12.345678}
        response = client.post("/products", json=data, headers=auth_headers)
        assert response.status_code == 200

        returned_price = response.json()["price"]
        assert isinstance(returned_price, (int, float))

    @patch("app.routes.publish_event_safe")
    def test_update_product_publishes_event(
        self, mock_publish, client, auth_headers, created_product
    ):
        """Test that updating a product publishes the correct event"""
        product_id = created_product["id"]

        mock_publish.reset_mock()

        update_data = {"name": "Produit Mis À Jour"}
        response = client.put(
            f"/products/{product_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200

        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][1] == "product.updated"
        event_data = call_args[0][2]
        assert event_data["name"] == "Produit Mis À Jour"

    @patch("app.routes.publish_event_safe")
    def test_delete_product_publishes_event(
        self, mock_publish, client, auth_headers, created_product
    ):
        """Test that deleting a product publishes the correct event"""
        product_id = created_product["id"]

        mock_publish.reset_mock()

        response = client.delete(f"/products/{product_id}", headers=auth_headers)
        assert response.status_code == 200

        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][1] == "product.deleted"

    def test_concurrent_product_operations(self, client, auth_headers, created_product):
        """Test handling concurrent operations on the same product"""
        product_id = created_product["id"]

        update1 = {"stock": 50}
        update2 = {"stock": 75}

        response1 = client.put(
            f"/products/{product_id}", json=update1, headers=auth_headers
        )
        response2 = client.put(
            f"/products/{product_id}", json=update2, headers=auth_headers
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_malformed_json_request(self, client, auth_headers):
        """Test API behavior with malformed JSON"""
        response = client.post(
            "/products",
            data='{"name": "Test"',
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_health_endpoint(self, client):
        """Test health check endpoint if available"""
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
        else:
            assert response.status_code == 404

    def test_messaging_health_endpoint(self, client):
        """Test messaging health endpoint if available"""
        response = client.get("/health/messaging")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "message_broker" in data
        else:
            assert response.status_code == 404


class TestProductUtilities:
    """Utility functions for product testing"""

    @staticmethod
    def create_test_product(client, auth_headers, **kwargs):
        """Helper function to create a test product with default values"""
        default_data = {
            "name": "Test Product",
            "price": 10.0,
            "description": "Test description",
            "color": "Blue",
            "stock": 10,
        }
        default_data.update(kwargs)

        response = client.post("/products", json=default_data, headers=auth_headers)
        assert response.status_code == 200
        return response.json()

    @staticmethod
    def assert_product_fields(product_data, expected_data):
        """Helper function to assert product fields match expected data"""
        for key, value in expected_data.items():
            assert product_data.get(key) == value

    @staticmethod
    def create_products_batch(client, auth_headers, count=5):
        """Helper to create multiple products for testing"""
        products = []
        for i in range(count):
            data = {
                "name": f"Batch Product {i}",
                "price": 10.0 + i,
                "stock": 100 - i * 10,
            }
            response = client.post("/products", json=data, headers=auth_headers)
            assert response.status_code == 200
            products.append(response.json())
        return products
