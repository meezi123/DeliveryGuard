from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict():
    payload = {
        "customer_state": "SP",
        "primary_payment_type": "credit_card",
        "number_of_items": 2,
        "number_of_unique_products": 2,
        "number_of_unique_sellers": 1,
        "total_product_price": 250.0,
        "total_freight_value": 45.0,
        "average_product_weight_g": 1200.0,
        "average_product_length_cm": 30.0,
        "average_product_height_cm": 15.0,
        "average_product_width_cm": 20.0,
        "number_of_product_categories": 1,
        "total_payment_installments": 3,
        "total_payment_value": 295.0,
        "number_of_payment_records": 1,
        "order_purchase_timestamp": "2018-07-10T10:30:00",
        "order_approved_at": "2018-07-10T12:30:00",
        "order_estimated_delivery_date": "2018-07-22T00:00:00"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert "late_delivery_risk_score" in response.json()
    assert "risk_level" in response.json()