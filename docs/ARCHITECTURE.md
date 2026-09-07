# RetainIQ Architecture

```text
User
 ↓
HTML / CSS / JavaScript
 ↓
Flask Application
 ├── Authentication
 ├── Prediction Engine
 ├── Analytics Engine
 └── Retention Engine
 ↓
MySQL
```

## ML Flow
```text
Raw Data
 ↓
Cleaning / Feature Preparation
 ↓
ML Model
 ↓
Churn Probability
 ↓
Risk Classification
 ↓
SHAP Explanation
 ↓
Retention Recommendation
```

## Main Database Entities
- `users`
- `datasets`
- `customers`
- `predictions`
- `customer_explanations`

Dataset and customer access is scoped to the authenticated user.

## Batch Design
Bulk prediction avoids calculating SHAP for every customer for performance reasons. SHAP is generated when an individual customer is opened.
