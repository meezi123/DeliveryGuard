# Leakage Policy

The model predicts at order approval time. Therefore, it must use only information available at or before that time.

## Never use as features

- order_delivered_customer_date
- order_delivered_carrier_date
- order_status
- review_score
- review comments
- final delivery duration
- any field created after delivery

## Allowed future candidate features

- customer location
- seller location
- product category and dimensions
- price and freight value
- payment type
- purchase date and approval date features
- estimated delivery date
- customer-to-seller distance