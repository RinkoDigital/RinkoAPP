from app.models import Client, Company, Delivery


def rate_for_client(company: Company, client: Client) -> int:
    return client.default_rate_cents if client.default_rate_cents is not None else company.default_rate_cents


def compute_amount_due_cents(delivery: Delivery) -> int:
    return delivery.payable_count * delivery.rate_cents
