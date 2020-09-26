from django.urls import path

from kunal_advertising.receipt_invoice.views import ReceiptInvoicePreview, DownLoadReceipt

urlpatterns = [
    path("preview/", ReceiptInvoicePreview.as_view(), name="receipt_invoice_preview"),
    path("download-receipt/", DownLoadReceipt.as_view(), name="download_receipt"),
]
