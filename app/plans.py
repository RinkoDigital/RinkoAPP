"""Plan tiers and what they gate.

Only value-added convenience is gated — never the driver's own data. JSON
work reports, CSV export, and the payment ledger are free on every plan,
full stop; that's the product's independence promise. Free vs. Pro only
changes formatted document generation and how much evidence storage a
driver gets before Rinko's own infra costs matter.

No billing integration exists yet (same call the MVP made about payments
in general — no Stripe/Wise at this stage). `Driver.plan` is a manual
flag for now, flipped via POST /account/plan; wiring it to real billing
is future work.
"""

from app.models import PlanTier

FREE_EVIDENCE_PER_SESSION = 3

PLAN_LIMITS = {
    PlanTier.FREE: {
        "docx_export": False,
        "evidence_per_session": FREE_EVIDENCE_PER_SESSION,
    },
    PlanTier.PRO: {
        "docx_export": True,
        "evidence_per_session": None,  # unlimited
    },
}


def can_export_docx(plan: PlanTier) -> bool:
    return PLAN_LIMITS[plan]["docx_export"]


def evidence_limit(plan: PlanTier) -> int | None:
    return PLAN_LIMITS[plan]["evidence_per_session"]
