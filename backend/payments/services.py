"""
INCOME – Payment processing service.
Atomic payment allocation, verification, reversal.
All amounts are Decimal. Never use float.
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import Payment, PaymentAllocation, PaymentReversal, PaymentStatus
from finance.models import StudentCharge
from finance.utils import recalculate_charge_status, quantize

ZERO = Decimal("0.00")


def allocate_payment(payment: Payment, allocations: list[dict]) -> list[PaymentAllocation]:
    """
    Allocate a confirmed payment across one or more student charges.

    allocations: list of {"charge_id": uuid, "amount": Decimal}

    Rules enforced:
    - Total allocated <= payment.amount
    - Each charge cannot be over-settled
    - Uses SELECT FOR UPDATE to prevent race conditions
    """
    with transaction.atomic():
        # Re-fetch the payment with a row lock
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != PaymentStatus.CONFIRMED:
            raise ValueError("Only confirmed payments can be allocated.")

        total_requested = quantize(sum(Decimal(str(a["amount"])) for a in allocations))

        # Verify total <= payment amount
        existing_alloc = PaymentAllocation.objects.filter(
            payment=payment, is_reversed=False
        ).aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount_allocated"))
        existing_total = quantize(existing_alloc.get("total") or ZERO)

        if existing_total + total_requested > payment.amount:
            raise ValueError(
                f"Allocation of {total_requested} would exceed payment amount "
                f"{payment.amount} (already allocated: {existing_total})."
            )

        created = []
        for alloc in allocations:
            charge = StudentCharge.objects.select_for_update().get(pk=alloc["charge_id"])
            amount = quantize(Decimal(str(alloc["amount"])))

            if amount <= ZERO:
                raise ValueError("Allocation amount must be positive.")

            # Check charge belongs to same student
            if charge.student_id != payment.student_id:
                raise ValueError("Cannot allocate payment to another student's charge.")

            # Check over-settlement
            already_paid = quantize(
                PaymentAllocation.objects.filter(
                    charge=charge, payment__status=PaymentStatus.CONFIRMED, is_reversed=False
                ).aggregate(
                    total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount_allocated")
                )["total"] or ZERO
            )

            if already_paid + amount > charge.net_amount:
                raise ValueError(
                    f"Charge '{charge.description}' would be over-settled. "
                    f"Net: {charge.net_amount}, Already paid: {already_paid}, Requested: {amount}"
                )

            pa = PaymentAllocation.objects.create(
                payment=payment,
                charge=charge,
                amount_allocated=amount,
            )
            created.append(pa)

            # Update charge status
            recalculate_charge_status(charge)

        return created


def confirm_payment(payment: Payment, verified_by) -> Payment:
    """
    Marks a payment as confirmed. Only for pending payments.
    Separation of duties: the person who recorded cannot confirm
    if the school enforces this rule.
    """
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot confirm a payment with status '{payment.status}'.")

        payment.status = PaymentStatus.CONFIRMED
        payment.verified_by = verified_by
        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])

    return payment


def reject_payment(payment: Payment, rejected_by, reason: str) -> Payment:
    """Marks a payment as rejected."""
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot reject a payment with status '{payment.status}'.")

        if not reason.strip():
            raise ValueError("A rejection reason is required.")

        payment.status = PaymentStatus.REJECTED
        payment.rejected_by = rejected_by
        payment.rejected_at = timezone.now()
        payment.rejection_reason = reason
        payment.save(update_fields=[
            "status", "rejected_by", "rejected_at", "rejection_reason", "updated_at"
        ])

    return payment


def reverse_payment(payment: Payment, reversed_by, reason: str) -> PaymentReversal:
    """
    Reverses a confirmed payment.
    Undoes all payment allocations and recalculates charge statuses.
    """
    if not reason.strip():
        raise ValueError("A reversal reason is required.")

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != PaymentStatus.CONFIRMED:
            raise ValueError(f"Can only reverse confirmed payments (status: {payment.status}).")

        # Mark all allocations as reversed
        allocations = PaymentAllocation.objects.select_for_update().filter(
            payment=payment, is_reversed=False
        )
        charge_ids = list(allocations.values_list("charge_id", flat=True))
        allocations.update(is_reversed=True)

        # Update payment status
        payment.status = PaymentStatus.REVERSED
        payment.save(update_fields=["status", "updated_at"])

        # Recalculate all affected charge statuses
        for charge_id in charge_ids:
            charge = StudentCharge.objects.get(pk=charge_id)
            recalculate_charge_status(charge)

        reversal = PaymentReversal.objects.create(
            payment=payment,
            reason=reason,
            reversed_by=reversed_by,
        )

    return reversal
