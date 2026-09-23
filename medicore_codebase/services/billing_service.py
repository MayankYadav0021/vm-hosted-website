class BillingService:
    def __init__(self):
        self.invoices = {}

    def create_invoice(self, invoice_id, patient_id, amount):
        if amount <= 0:
            raise ValueError("Invoice amount must be positive")

        invoice = {
            "invoice_id": invoice_id,
            "patient_id": patient_id,
            "amount": amount,
            "status": "PENDING",
        }

        self.invoices[invoice_id] = invoice
        return invoice

    def mark_paid(self, invoice_id):
        invoice = self.invoices.get(invoice_id)

        if invoice is None:
            raise ValueError("Invoice not found")

        invoice["status"] = "PAID"
        return invoice
