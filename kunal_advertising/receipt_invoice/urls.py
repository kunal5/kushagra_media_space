from django.urls import path

from kunal_advertising.receipt_invoice.views import ReceiptInvoicePreview

urlpatterns = [
    path("preview/", ReceiptInvoicePreview.as_view(), name="receipt_invoice_preview"),
]
