from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, View

from kunal_advertising.receipt_invoice.models import ReceiptInvoice
from kunal_advertising.receipt_invoice.constants import (
    NO_PAPER_FOUND,
    NO_DATE_FOUND,
    CACHE_KEY_FOR_TOTAL_AMOUNT,
    CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS,
)


class RedirectToAdminView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect("/admin/")


class ReceiptInvoicePreview(TemplateView):
    template_name = "create_pdf_invoice.html"

    def get(self, request, *args, **kwargs):
        try:
            receipt_id = request.GET.get("receipt_id") or int(args[0])
            receipt_invoice = ReceiptInvoice.objects.get(pk=receipt_id)
        except (ValueError, ReceiptInvoice.DoesNotExist):
            return HttpResponseNotFound()

        if not receipt_invoice.total_papers.all():
            return JsonResponse(
                {"No paper Found": NO_PAPER_FOUND.format(client_name=receipt_invoice.client_name)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            for paper in receipt_invoice.total_papers.all():
                if not paper.all_dates.all():
                    return JsonResponse(
                        {"No dates found": NO_DATE_FOUND.format(paper_name=paper.name)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        context = self.get_context_data(**kwargs)
        context["receipt_invoice"] = receipt_invoice

        cache_key_for_total_amount = CACHE_KEY_FOR_TOTAL_AMOUNT.format(client_id=receipt_invoice.id)
        cache_key_for_total_amount_in_words = CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS.format(client_id=receipt_invoice.id)
        context["total_amount_charged"] = cache.get(cache_key_for_total_amount)
        context["total_amount_charged_in_words"] = cache.get(cache_key_for_total_amount_in_words)

        return render(
            request,
            template_name=ReceiptInvoicePreview.template_name,
            context=context,
            content_type="text/html",
            status=status.HTTP_200_OK,
        )
