# DeliveryGuard: Problem Definition

## Business problem

Late deliveries damage customer trust, create support tickets, and increase negative reviews. Operations teams cannot manually inspect every order.

## Prediction objective

At the moment an order is approved, predict whether it is likely to be delivered after its estimated delivery date.

## Unit of prediction

One row represents one order.

## Target variable

late_delivery = 1 when:

order_delivered_customer_date > order_estimated_delivery_date

late_delivery = 0 otherwise.

## Eligible training data

Only orders with status "delivered".

## Prediction time

Immediately after order approval.

## Stakeholder

Marketplace operations manager.

## Business action

Orders with high late-delivery risk can be prioritized for seller follow-up, carrier tracking, or proactive customer communication.