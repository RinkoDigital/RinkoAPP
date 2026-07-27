from fastapi import HTTPException

from app.models import Delivery, DeliveryStatus
from app.schemas import DeliveryProof


def build_delivery_proof(delivery: Delivery) -> DeliveryProof:
    if delivery.status != DeliveryStatus.VALIDATED:
        raise HTTPException(
            status_code=409, detail="Delivery has not been validated yet — no proof to show"
        )

    packages = delivery.packages
    return DeliveryProof(
        proof_number=f"PRF-{delivery.id.hex[:8].upper()}",
        company_name=delivery.company.name,
        driver_name=delivery.driver.name,
        client_name=delivery.client.name,
        batch_date=delivery.batch_date,
        assigned_count=delivery.assigned_count,
        exceptions_count=delivery.exceptions_count,
        payable_count=delivery.payable_count,
        rate_cents=delivery.rate_cents,
        amount_due_cents=delivery.amount_due_cents,
        validated_at=delivery.validated_at,
        payment_status=delivery.payment_status,
        paid_amount_cents=delivery.paid_amount_cents,
        paid_at=delivery.paid_at,
        packages_logged=len(packages),
        packages_with_photo=sum(1 for p in packages if p.pod_photo_url is not None),
        packages_with_scan_code=sum(1 for p in packages if p.pod_scan_code is not None),
    )
