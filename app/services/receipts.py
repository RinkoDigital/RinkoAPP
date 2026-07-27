from fastapi import HTTPException

from app.models import Delivery, PaymentStatus
from app.schemas import PaymentReceipt


def build_payment_receipt(delivery: Delivery) -> PaymentReceipt:
    if delivery.payment_status != PaymentStatus.PAID:
        raise HTTPException(status_code=409, detail="Delivery has not been marked as paid yet")

    packages = delivery.packages
    return PaymentReceipt(
        receipt_number=f"RCT-{delivery.id.hex[:8].upper()}",
        company_name=delivery.company.name,
        driver_name=delivery.driver.name,
        client_name=delivery.client.name,
        batch_date=delivery.batch_date,
        assigned_count=delivery.assigned_count,
        exceptions_count=delivery.exceptions_count,
        payable_count=delivery.payable_count,
        rate_cents=delivery.rate_cents,
        amount_due_cents=delivery.amount_due_cents,
        paid_amount_cents=delivery.paid_amount_cents,
        paid_at=delivery.paid_at,
        validated_at=delivery.validated_at,
        packages_logged=len(packages),
        packages_with_photo=sum(1 for p in packages if p.pod_photo_url is not None),
        packages_with_scan_code=sum(1 for p in packages if p.pod_scan_code is not None),
    )
