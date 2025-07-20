from fastapi.testclient import TestClient
from app.main import app  # modifie si ton fichier s'appelle autrement
import os

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

client = TestClient(app)

created_product_id = None


def test_create_product():
    global created_product_id
    response = client.post(
        "/products",
        headers=HEADERS,
        json={
            "name": "Test Produit",
            "price": 12.34,
            "description": "Description test",
            "color": "Rouge",
            "stock": 5,
            "created_at": "2025-07-11T08:01:18.595Z",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Produit"
    created_product_id = data["id"]


def test_get_product():
    response = client.get(f"/products/{created_product_id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_product_id


def test_list_products():
    response = client.get("/products", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_product():
    response = client.put(
        f"/products/{created_product_id}",
        headers=HEADERS,
        json={"name": "Produit Modifié"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Produit Modifié"


def test_delete_product():
    response = client.delete(f"/products/{created_product_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["message"] == "Produit supprimé avec succès"


def test_protected_route_without_token():
    response = client.get("/products")
    assert response.status_code == 403
