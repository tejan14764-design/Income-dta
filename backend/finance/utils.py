"""
INCOME – Financial calculation utilities.
All calculations use Decimal arithmetic.
Never use float for currency.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from django.db import transaction

ZERO = Decimal("0.00")
HUNDRED = Decimal("100.00")


def quantize(value: Decimal) -> Decimal:
    """Round to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_student_financial_summary(student, academic_year=None):
    """
    Returns the complete financial summary for a student.
    If academic_year is None, returns the current active year summary.
    """
    from finance.models import StudentCharge
    from payments.models import PaymentAllocation, Payment

    charges_qs = StudentCharge.objects.filter(
        student=student, is_active=True
    )
    if academic_year:
        charges_qs = charges_qs.filter(academic_year=academic_year)

    # Aggregate base amounts
    agg = charges_qs.aggregate(
        total_base=Sum("base_amount"),
        total_discount=Sum("discount_amount"),
        total_waiver=Sum("waiver_amount"),
    )

    total_base = agg["total_base"] or ZERO
    total_discount = agg["total_discount"] or ZERO
    total_waiver = agg["total_waiver"] or ZERO
    total_expected = quantize(max(ZERO, total_base - total_discount - total_waiver))

    # Confirmed payments only
    alloc_qs = PaymentAllocation.objects.filter(
        charge__student=student,
        payment__status="confirmed",
    )
    if academic_year:
        alloc_qs = alloc_qs.filter(charge__academic_year=academic_year)

    alloc_agg = alloc_qs.aggregate(total_allocated=Sum("amount_allocated"))
    total_paid = quantize(alloc_agg["total_allocated"] or ZERO)

    outstanding = quantize(max(ZERO, total_expected - total_paid))
    credit_balance = quantize(max(ZERO, total_paid - total_expected))

    if total_expected > ZERO:
        progress = quantize((total_paid / total_expected) * HUNDRED)
    else:
        progress = HUNDRED if total_paid > ZERO else ZERO

    # Payment status
    if total_paid >= total_expected and total_expected > ZERO:
        payment_status = "fully_paid"
    elif total_paid > ZERO:
        payment_status = "partially_paid"
    else:
        payment_status = "unpaid"

    # Charge breakdown
    charge_data = []
    for charge in charges_qs.select_related("category"):
        charge_alloc = PaymentAllocation.objects.filter(
            charge=charge, payment__status="confirmed"
        ).aggregate(paid=Sum("amount_allocated"))
        charge_paid = quantize(charge_alloc["paid"] or ZERO)
        charge_net = charge.net_amount
        charge_outstanding = quantize(max(ZERO, charge_net - charge_paid))

        charge_data.append({
            "id": str(charge.id),
            "description": charge.description,
            "category": charge.category.name,
            "base_amount": str(charge.base_amount),
            "discount_amount": str(charge.discount_amount),
            "waiver_amount": str(charge.waiver_amount),
            "net_amount": str(charge_net),
            "amount_paid": str(charge_paid),
            "outstanding": str(charge_outstanding),
            "is_mandatory": charge.is_mandatory,
            "due_date": str(charge.due_date) if charge.due_date else None,
            "status": charge.status,
        })

    return {
        "total_expected": str(total_expected),
        "total_paid": str(total_paid),
        "outstanding": str(outstanding),
        "credit_balance": str(credit_balance),
        "payment_progress": str(progress),
        "payment_status": payment_status,
        "charges": charge_data,
    }


def apply_template_to_student(template, student, academic_year, assigned_by):
    """
    Copies all items from a FeeTemplate into individual StudentCharge records.
    Does NOT modify existing charges.
    Returns the StudentFeeAssignment created.
    """
    from finance.models import StudentFeeAssignment, StudentCharge

    with transaction.atomic():
        assignment, created = StudentFeeAssignment.objects.get_or_create(
            student=student,
            academic_year=academic_year,
            defaults={
                "school": student.school,
                "template": template,
                "assigned_by": assigned_by,
            }
        )

        for item in template.items.filter():
            StudentCharge.objects.get_or_create(
                school=student.school,
                student=student,
                academic_year=academic_year,
                assignment=assignment,
                category=item.category,
                description=item.description,
                defaults={
                    "base_amount": item.amount,
                    "is_mandatory": item.is_mandatory,
                    "due_date": item.due_date,
                    "created_by": assigned_by,
                }
            )

        return assignment


def recalculate_charge_status(charge):
    """
    Recalculates and saves the status of a single StudentCharge
    based on confirmed payment allocations.
    """
    from payments.models import PaymentAllocation
    from django.utils import timezone

    alloc_agg = PaymentAllocation.objects.filter(
        charge=charge, payment__status="confirmed"
    ).aggregate(total=Sum("amount_allocated"))

    amount_paid = quantize(alloc_agg["total"] or ZERO)
    net = charge.net_amount

    if net == ZERO:
        new_status = "fully_paid"
    elif amount_paid >= net:
        new_status = "fully_paid"
    elif amount_paid > ZERO:
        new_status = "partially_paid"
    elif charge.due_date and charge.due_date < timezone.now().date():
        new_status = "overdue"
    else:
        new_status = "unpaid"

    charge.status = new_status
    charge.save(update_fields=["status", "updated_at"])
    return new_status
