"""
INCOME – Receipt generation service.
Generates unique receipt numbers and PDF receipts.
"""

import io
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import Receipt, ReceiptPrintLog
from finance.utils import get_student_financial_summary

RECEIPT_WIDTH = 80 * mm
RECEIPT_HEIGHT = 200 * mm  # Variable height thermal receipt


def generate_receipt_number(school) -> str:
    """Generate a sequential, unique receipt number per school."""
    last = Receipt.objects.filter(school=school).order_by("-generated_at").first()
    if last and last.receipt_number:
        try:
            num = int(last.receipt_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"RCP-{school.code.upper()}-{num:06d}"


def generate_receipt_for_payment(payment, generated_by) -> Receipt:
    """
    Creates a Receipt record for a confirmed payment.
    If a receipt already exists, returns it without creating a duplicate.
    """
    with transaction.atomic():
        existing = Receipt.objects.filter(payment=payment).first()
        if existing:
            return existing

        from academics.models import Enrollment
        enrollment = Enrollment.objects.filter(
            student=payment.student, is_active=True
        ).select_related("class_ref").first()
        class_name = enrollment.class_ref.name if enrollment else ""

        summary = get_student_financial_summary(payment.student, payment.academic_year)

        # Build fee descriptions from payment allocations
        fee_descriptions = []
        for alloc in payment.allocations.select_related("charge"):
            fee_descriptions.append({
                "description": alloc.charge.description,
                "amount": str(alloc.amount_allocated),
            })

        receipt = Receipt.objects.create(
            school=payment.school,
            payment=payment,
            receipt_number=generate_receipt_number(payment.school),
            student_name=payment.student.full_name,
            student_admission_number=payment.student.admission_number,
            class_name=class_name,
            academic_year_name=payment.academic_year.name,
            payment_method=payment.get_payment_method_display(),
            amount_paid=payment.amount,
            outstanding_after=Decimal(summary["outstanding"]),
            fee_descriptions=fee_descriptions,
            transaction_reference=payment.transaction_reference,
            cashier_name=payment.recorded_by.get_full_name() if payment.recorded_by else "N/A",
            generated_by=generated_by,
        )

        # Log the original print
        ReceiptPrintLog.objects.create(
            receipt=receipt,
            printed_by=generated_by,
            print_type="original",
        )

    return receipt


def generate_receipt_pdf(receipt: Receipt) -> bytes:
    """
    Generate an 80mm thermal receipt PDF.
    Returns raw PDF bytes.
    """
    school = receipt.school
    school_settings = getattr(school, "settings", None)
    footer_text = school_settings.receipt_footer if school_settings else "Thank you for your payment."

    buffer = io.BytesIO()
    page_size = (RECEIPT_WIDTH, RECEIPT_HEIGHT)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=4 * mm,
        rightMargin=4 * mm,
        topMargin=4 * mm,
        bottomMargin=4 * mm,
    )

    styles = getSampleStyleSheet()
    center_style = ParagraphStyle("center", alignment=TA_CENTER, fontSize=8, leading=10)
    bold_center = ParagraphStyle("bold_center", alignment=TA_CENTER, fontSize=9, leading=11, fontName="Helvetica-Bold")
    small_style = ParagraphStyle("small", alignment=TA_LEFT, fontSize=7, leading=9)
    right_style = ParagraphStyle("right", alignment=TA_RIGHT, fontSize=7, leading=9)
    large_center = ParagraphStyle("large", alignment=TA_CENTER, fontSize=11, leading=13, fontName="Helvetica-Bold")

    story = []

    # School header
    story.append(Paragraph(school.name.upper(), large_center))
    if school.address:
        story.append(Paragraph(school.address, center_style))
    if school.phone_number:
        story.append(Paragraph(f"Tel: {school.phone_number}", center_style))
    if school.email:
        story.append(Paragraph(school.email, center_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Paragraph("OFFICIAL RECEIPT", bold_center))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 2 * mm))

    # Receipt metadata
    meta_data = [
        ["Receipt No:", receipt.receipt_number],
        ["Date:", receipt.generated_at.strftime("%d/%m/%Y %H:%M")],
        ["Student:", receipt.student_name],
        ["Adm No:", receipt.student_admission_number],
        ["Class:", receipt.class_name or "—"],
        ["Acad. Year:", receipt.academic_year_name],
        ["Method:", receipt.payment_method],
    ]
    if receipt.transaction_reference:
        meta_data.append(["Ref:", receipt.transaction_reference])

    for row in meta_data:
        tbl = Table([[Paragraph(row[0], small_style), Paragraph(row[1], small_style)]],
                    colWidths=[25 * mm, 43 * mm])
        tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 1),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                                  ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5)]))
        story.append(tbl)

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

    # Fee breakdown
    if receipt.fee_descriptions:
        story.append(Paragraph("FEE BREAKDOWN", bold_center))
        for fee in receipt.fee_descriptions:
            fee_row = Table(
                [[Paragraph(fee["description"], small_style),
                  Paragraph(f"NLe {fee['amount']}", right_style)]],
                colWidths=[45 * mm, 23 * mm],
            )
            fee_row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 1),
                                          ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                                          ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                                          ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5)]))
            story.append(fee_row)

        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

    # Total
    total_row = Table(
        [[Paragraph("TOTAL PAID:", bold_center),
          Paragraph(f"NLe {receipt.amount_paid}", bold_center)]],
        colWidths=[35 * mm, 33 * mm],
    )
    total_row.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    story.append(total_row)

    outstanding_row = Table(
        [[Paragraph("Outstanding:", small_style),
          Paragraph(f"NLe {receipt.outstanding_after}", small_style)]],
        colWidths=[35 * mm, 33 * mm],
    )
    story.append(outstanding_row)

    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

    # Cashier
    story.append(Paragraph(f"Cashier: {receipt.cashier_name}", small_style))
    story.append(Spacer(1, 3 * mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(footer_text, center_style))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Powered by INCOME", center_style))

    doc.build(story)
    return buffer.getvalue()
