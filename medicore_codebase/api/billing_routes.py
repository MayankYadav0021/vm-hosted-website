from services.billing_service import BillingService

billing_service = BillingService()


def create_invoice(invoice_id, patient_id, amount):
    return billing_service.create_invoice(
        invoice_id,
        patient_id,
        amount,
    )


def mark_invoice_paid(invoice_id):
    return billing_service.mark_paid(invoice_id)
