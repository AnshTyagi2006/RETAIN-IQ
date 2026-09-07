# RetainIQ API Reference

## Authentication
- `POST /auth/register` — Register a user
- `POST /auth/login` — Login
- `GET /auth/logout` — Logout
- `GET /auth/me` — Current user

## Prediction
- `POST /predict` — Individual churn prediction
- `POST /analyze` — Analyze uploaded dataset
- `GET /sample-data` — Sample dataset workflow
- `POST /explain-customer` — Individual SHAP explanation

## Customers / Datasets
- `GET /customers/data` — Customer data
- `GET /datasets` — User's datasets
- `GET /datasets/<dataset_id>` — Authorized dataset

Protected routes require authentication. Dataset access is additionally checked against ownership.
