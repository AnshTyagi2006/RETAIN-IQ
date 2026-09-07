def _get(customer, *keys, default=None):
    for key in keys:
        if key in customer and customer[key] is not None:
            return customer[key]
    return default


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generate_retention_action(customer, risk_level):
    complain = int(_num(_get(customer, "complain", "Complain"), 0))
    satisfaction = _num(
        _get(customer, "satisfaction_score", "SatisfactionScore"), 0
    )
    days_since_order = _num(
        _get(customer, "days_since_last_order", "DaySinceLastOrder"), 0
    )

    if risk_level == "High Risk":
        if complain == 1:
            return {
                "action": "Service Recovery",
                "priority": "Immediate",
                "reason": "Customer has an active complaint.",
                "recommendation": (
                    "Contact the customer, resolve the complaint and "
                    "provide a recovery incentive if appropriate."
                )
            }
        if satisfaction > 0 and satisfaction <= 2:
            return {
                "action": "Satisfaction Recovery",
                "priority": "Immediate",
                "reason": "Customer has a low satisfaction score.",
                "recommendation": (
                    "Investigate the customer's experience and provide "
                    "a personalized recovery intervention."
                )
            }
        if days_since_order >= 30:
            return {
                "action": "Re-engagement Campaign",
                "priority": "Immediate",
                "reason": "Customer has been inactive for an extended period.",
                "recommendation": (
                    "Launch a personalized re-engagement campaign with "
                    "a relevant offer or reminder."
                )
            }
        return {
            "action": "Personalized Retention",
            "priority": "Immediate",
            "reason": "Customer has a high predicted churn risk.",
            "recommendation": (
                "Prioritize the customer for personalized retention "
                "outreach based on their strongest churn drivers."
            )
        }

    if risk_level == "Medium Risk":
        if complain == 1:
            return {
                "action": "Issue Follow-up",
                "priority": "High",
                "reason": "Customer has reported a complaint.",
                "recommendation": (
                    "Follow up on the customer's issue and prevent "
                    "further dissatisfaction."
                )
            }
        if days_since_order >= 30:
            return {
                "action": "Re-engagement",
                "priority": "High",
                "reason": "Customer activity appears to be declining.",
                "recommendation": (
                    "Use a targeted re-engagement message to encourage "
                    "the next purchase."
                )
            }
        if satisfaction > 0 and satisfaction <= 2:
            return {
                "action": "Experience Improvement",
                "priority": "High",
                "reason": "Customer satisfaction is low despite moderate churn risk.",
                "recommendation": (
                    "Address the customer's experience and use targeted "
                    "follow-up to prevent escalation."
                )
            }
        return {
            "action": "Targeted Engagement",
            "priority": "Medium",
            "reason": "Customer shows moderate churn risk.",
            "recommendation": (
                "Use targeted communication, relevant offers and "
                "engagement campaigns."
            )
        }

    return {
        "action": "Loyalty Nurturing",
        "priority": "Low",
        "reason": "Customer currently has relatively low churn risk.",
        "recommendation": (
            "Maintain engagement through loyalty benefits, "
            "personalized recommendations and regular communication."
        )
    }


def retention_action_to_recommendation(action):
    if not action:
        return ""
    return f'{action.get("action", "Retention")} — {action.get("recommendation", "")}'
