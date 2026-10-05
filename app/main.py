from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]

artifact = joblib.load(
    PROJECT_ROOT / "models" / "deliveryguard_logistic_pipeline.joblib"
)

model_pipeline = artifact["pipeline"]
selected_threshold = artifact["threshold"]
model_version = artifact["model_version"]


app = FastAPI(
    title="DeliveryGuard API",
    description="Predicts e-commerce late-delivery risk.",
    version=model_version
)


class OrderInput(BaseModel):
    customer_state: str = Field(
        examples=["SP"]
    )
    primary_payment_type: Optional[str] = Field(
        default="credit_card"
    )

    number_of_items: int = Field(
        gt=0,
        examples=[2]
    )
    number_of_unique_products: int = Field(
        gt=0,
        examples=[2]
    )
    number_of_unique_sellers: int = Field(
        gt=0,
        examples=[1]
    )

    total_product_price: float = Field(
        ge=0,
        examples=[250.0]
    )
    total_freight_value: float = Field(
        ge=0,
        examples=[45.0]
    )

    average_product_weight_g: Optional[float] = Field(
        default=None,
        ge=0,
        examples=[1200.0]
    )
    average_product_length_cm: Optional[float] = Field(
        default=None,
        ge=0,
        examples=[30.0]
    )
    average_product_height_cm: Optional[float] = Field(
        default=None,
        ge=0,
        examples=[15.0]
    )
    average_product_width_cm: Optional[float] = Field(
        default=None,
        ge=0,
        examples=[20.0]
    )

    number_of_product_categories: int = Field(
        ge=0,
        examples=[1]
    )
    total_payment_installments: Optional[float] = Field(
        default=1,
        ge=0
    )
    total_payment_value: Optional[float] = Field(
        default=295.0,
        ge=0
    )
    number_of_payment_records: Optional[float] = Field(
        default=1,
        ge=0
    )

    order_purchase_timestamp: datetime
    order_approved_at: datetime
    order_estimated_delivery_date: datetime


def build_feature_row(order: OrderInput) -> pd.DataFrame:
    purchase_time = order.order_purchase_timestamp
    approval_time = order.order_approved_at
    estimated_date = order.order_estimated_delivery_date

    approval_delay_hours = (
        approval_time - purchase_time
    ).total_seconds() / 3600

    estimated_delivery_days = (
        estimated_date - approval_time
    ).total_seconds() / 86400

    estimated_delivery_days_invalid = int(
        estimated_delivery_days < 0
    )

    if estimated_delivery_days_invalid == 1:
        estimated_delivery_days = np.nan

    total_order_cost = (
        order.total_product_price
        + order.total_freight_value
    )

    freight_ratio = (
        order.total_freight_value / total_order_cost
        if total_order_cost > 0
        else np.nan
    )

    average_item_price = (
        order.total_product_price / order.number_of_items
    )

    product_dimensions_missing = int(
        any(
            value is None
            for value in [
                order.average_product_weight_g,
                order.average_product_length_cm,
                order.average_product_height_cm,
                order.average_product_width_cm
            ]
        )
    )

    payment_information_missing = int(
        any(
            value is None
            for value in [
                order.total_payment_installments,
                order.total_payment_value,
                order.number_of_payment_records,
                order.primary_payment_type
            ]
        )
    )

    average_product_volume_cm3 = None

    if not product_dimensions_missing:
        average_product_volume_cm3 = (
            order.average_product_length_cm
            * order.average_product_height_cm
            * order.average_product_width_cm
        )

    return pd.DataFrame([{
        "customer_state": order.customer_state,
        "primary_payment_type": order.primary_payment_type,
        "number_of_items": order.number_of_items,
        "number_of_unique_products": order.number_of_unique_products,
        "number_of_unique_sellers": order.number_of_unique_sellers,
        "total_product_price": order.total_product_price,
        "total_freight_value": order.total_freight_value,
        "average_product_weight_g": order.average_product_weight_g,
        "average_product_length_cm": order.average_product_length_cm,
        "average_product_height_cm": order.average_product_height_cm,
        "average_product_width_cm": order.average_product_width_cm,
        "number_of_product_categories": (
            order.number_of_product_categories
        ),
        "total_payment_installments": (
            order.total_payment_installments
        ),
        "total_payment_value": order.total_payment_value,
        "number_of_payment_records": (
            order.number_of_payment_records
        ),
        "purchase_month": purchase_time.month,
        "purchase_day_of_week": purchase_time.weekday(),
        "purchase_hour": purchase_time.hour,
        "approval_delay_hours": approval_delay_hours,
        "estimated_delivery_days": estimated_delivery_days,
        "estimated_delivery_days_invalid": (
            estimated_delivery_days_invalid
        ),
        "total_order_cost": total_order_cost,
        "freight_ratio": freight_ratio,
        "average_item_price": average_item_price,
        "average_product_volume_cm3": (
            average_product_volume_cm3
        ),
        "product_dimensions_missing": (
            product_dimensions_missing
        ),
        "payment_information_missing": (
            payment_information_missing
        )
    }])


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_name": "Logistic Regression",
        "model_version": model_version
    }


@app.post("/predict")
def predict(order: OrderInput):
    feature_row = build_feature_row(order)

    risk_score = float(
        model_pipeline.predict_proba(feature_row)[0, 1]
    )

    predicted_late_delivery = int(
        risk_score >= selected_threshold
    )

    if risk_score < 0.30:
        risk_level = "Low"
        recommended_action = (
            "Continue normal order workflow."
        )
    elif risk_score < 0.60:
        risk_level = "Medium"
        recommended_action = (
            "Monitor seller and carrier progress."
        )
    else:
        risk_level = "High"
        recommended_action = (
            "Prioritize seller and carrier follow-up."
        )

    return {
        "late_delivery_risk_score": round(risk_score, 4),
        "predicted_late_delivery": predicted_late_delivery,
        "risk_level": risk_level,
        "selected_threshold": selected_threshold,
        "recommended_action": recommended_action
    }