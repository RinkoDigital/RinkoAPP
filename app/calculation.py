from app.models import Company, Delivery


def compute_amount_due_cents(delivery: Delivery) -> int:
    return delivery.rate_cents * delivery.package_count


def rate_for_company(company: Company) -> int:
    return company.default_rate_cents
