from dataclasses import dataclass

@dataclass
class PriceBreakdown:
    weight_lbs: int
    price_per_lb_cents: int
    service_fee_cents: int
    delivery_fee_cents: int
    tax_rate_bp: int
    subtotal_cents: int
    tax_cents: int
    total_cents: int

def calc_price(
    weight_lbs: int,
    price_per_lb_cents: int = 175,
    service_fee_cents: int = 300,
    delivery_fee_cents: int = 500,
    tax_rate_bp: int = 700,
) -> PriceBreakdown:
    if weight_lbs <= 0:
        raise ValueError("weight_lbs must be greater than 0")

    wash_fold_cents = weight_lbs * price_per_lb_cents
    subtotal_cents = wash_fold_cents + service_fee_cents + delivery_fee_cents

    tax_cents = (subtotal_cents * tax_rate_bp) // 10_000
    total_cents = subtotal_cents + tax_cents

    return PriceBreakdown(
        weight_lbs=weight_lbs,
        price_per_lb_cents=price_per_lb_cents,
        service_fee_cents=service_fee_cents,
        delivery_fee_cents=delivery_fee_cents,
        tax_rate_bp=tax_rate_bp,
        subtotal_cents=subtotal_cents,
        tax_cents=tax_cents,
        total_cents=total_cents,
    )
