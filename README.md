# RetainIQ — Customer Retention Intelligence Platform

RetainIQ is an end-to-end ML platform for predicting customer churn, explaining predictions, segmenting customer risk, and recommending retention actions.

## Features

- User authentication and secure sessions
- Individual and batch churn prediction
- Sample dataset workflow
- High / Medium / Low risk classification
- SHAP-based individual explanations
- Business analytics and customer segmentation
- Retention action recommendations
- MySQL persistence
- Per-user dataset isolation

## Technology

Python, Flask, Pandas, NumPy, Scikit-learn, XGBoost, SHAP, MySQL, HTML/CSS/JavaScript, Pytest.

## Risk Levels

- `>= 0.70` → High
- `0.40–<0.70` → Medium
- `< 0.40` → Low

## 🖥️ Screenshots

### Landing Page

![RetainIQ Landing Page](docs/screenshots/01-landingpage.png)

### Bulk Retention Dashboard

![RetainIQ Bulk Dashboard](docs/screenshots/02%20-bulkdashboard.png)

### Customer Analysis

![RetainIQ Customer Analysis](docs/screenshots/03%20-customeranalysis.png)

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Testing

```bash
python -m pytest tests/test_retainiq_smoke.py -v
python -m pytest tests/security.py -v
```

Current validation: **30/30 automated tests passed** (22 smoke + 8 ownership/security).

## Core Flow

```text
Dataset → Prediction → Risk → Explanation → Retention Action
```

## Deployment

RetainIQ is deployment-ready and can be hosted as a public web application.

The included deployment configuration supports a production Flask server and a persistent MySQL database.

## 👨‍💻 About the Author

### Ansh Tyagi

B.Tech **Artificial Intelligence & Data Science** student focused on building practical AI systems that combine **machine learning, explainability, backend engineering, and real-world decision-making**.

RetainIQ was built around a simple idea:

> **Don't just predict the problem. Explain it. Prioritize it. Act on it.**

---

<div align="center">

## ⭐ RetainIQ

### **Predict. Explain. Prioritize. Act.**

*Turning ML predictions into retention decisions.*

</div>

