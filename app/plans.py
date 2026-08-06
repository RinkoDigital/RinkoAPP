"""Plan tiers and what they gate.

Only value-added convenience was ever meant to be gated — never the
driver's own data. JSON work reports, CSV export, and the payment ledger
are free on every plan, full stop; that's the product's independence
promise.

BILLING IS CURRENTLY DISABLED: there's no real payment integration
(Stripe or otherwise) yet, and the product decision — while still
validating whether the Work Report alone is worth paying for — is to
keep everything free rather than gate features behind a plan nobody can
actually buy. So every tier resolves to the same, unrestricted limits
below. `Driver.plan` and the `/account/plan` endpoint still exist (a
driver can be flagged "pro"), but it currently has no effect — flip
FREE's numbers back to real limits once billing exists.
"""

from app.models import PlanTier

PLAN_LIMITS = {
    PlanTier.FREE: {
        "docx_export": True,
        "evidence_per_session": None,  # unlimited
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
