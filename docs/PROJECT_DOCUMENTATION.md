# RetainIQ Project Documentation

## Problem
Businesses need to identify customers likely to churn and understand why they are at risk.

## Solution
RetainIQ combines churn prediction, explainable AI, business segmentation, and rule-based retention recommendations.

## Decision Pipeline
```text
Who may churn?
      ↓
How likely?
      ↓
Why?
      ↓
What should we do?
```

## Analytics
The dashboard analyzes:
- Satisfaction
- Complaints
- Tenure
- Preferred order category
- Risk distribution
- Churn probability
- Predicted churners

## Retention
Examples:
- High risk + complaint → Service Recovery
- High risk + low satisfaction → Satisfaction Recovery
- High risk + long inactivity → Re-engagement Campaign
- Medium risk + complaint → Issue Follow-up
- Low risk → Loyalty Nurturing

## Security
- Password hashing
- Authenticated sessions
- HTTPOnly / SameSite cookies
- Environment-based secrets
- User-scoped datasets
- Cross-user access prevention

## Testing
Automated validation: **30/30 tests passed**.

## Limitations
Recommendations are rule-based and should be validated against real business outcomes before automated customer intervention.

## Future Scope
CRM integration, campaign execution, model monitoring, drift detection, automated retraining, advanced reporting, and cloud deployment.
