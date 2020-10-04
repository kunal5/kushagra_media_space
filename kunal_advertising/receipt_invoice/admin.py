from django.db.models import Sum
from django.core.cache import cache
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe
from nested_admin.nested import NestedModelAdmin, NestedStackedInline
from django.contrib import admin

# Register your models here.
from num2words import num2words
from rangefilter.filter import DateRangeFilter

from kunal_advertising.receipt_invoice.admin_filters import UserFilter
from kunal_advertising.receipt_invoice.models import (
    ReceiptInvoice,
    PaperForAdvertisement,
    DatesForPaperAdvertisement,
)
from kunal_advertising.receipt_invoice.constants import CACHE_KEY_FOR_TOTAL_AMOUNT, CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS


class PaperForAdvertisementFormSet(BaseInlineFormSet):
    def save_existing(self, form, instance, commit=True):
        obj = super(PaperForAdvertisementFormSet, self).save_existing(form, instance, commit=True)
        # here you can add anything you need from the request
        obj.log_state_change(self.request.user)

        return obj


class DatesForPaperAdvertisementInline(NestedStackedInline):
    model = DatesForPaperAdvertisement
    classes = ("collapse",)
    extra = 1


class PaperForAdvertisementInline(NestedStackedInline):
    model = PaperForAdvertisement
    inlines = [
        DatesForPaperAdvertisementInline,
    ]
    exclude = [
        "amount_charged",
        "amount_charged_in_words",
    ]
    classes = ("collapse",)
    extra = 1
    formset = PaperForAdvertisementFormSet

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "amount_charged",
                "amount_charged_in_words",
            ]

        return []

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(PaperForAdvertisementInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


class ReceiptInvoiceAdmin(NestedModelAdmin):
    list_display = (
        "id",
        "client_name",
        "phone_number",
        "message_sent",
        "caption",
        "employee",
        "total_amount_charged",
        "generate_pdf",
    )
    list_select_related = ("created_by",)
    list_filter = (
        ("created_at", DateRangeFilter),
        UserFilter,
        "message_sent",
        "mode_of_payment",
    )
    search_fields = ("client_name",)
    fields = ("client_name", "address", "bank_name", "branch", "mode_of_payment", "phone_number", "caption")
    inlines = [
        PaperForAdvertisementInline,
    ]

    class Media:
        js = ("receipt_invoice_admin/js/admin/custom_admin.js",)

    def employee(self, obj):
        return obj.created_by.first_name + " " + obj.created_by.last_name

    employee.short_description = "Employee Name"

    def generate_pdf(self, obj):
        url = reverse("receipt_invoice_preview")
        return mark_safe("<a href='{0}?receipt_id={1}'>Click Here</a>".format(url, obj.id))

    def total_amount_charged(self, obj):
        cache_key_for_total_amount = CACHE_KEY_FOR_TOTAL_AMOUNT.format(client_id=obj.id)
        cache_key_for_total_amount_in_words = CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS.format(client_id=obj.id)
        total_amount = cache.get(cache_key_for_total_amount)
        total_amount_in_words = cache.get(cache_key_for_total_amount_in_words)

        if not (total_amount and total_amount_in_words):
            all_papers = obj.total_papers.all().aggregate(total_amount_charged=Sum("amount_charged"))
            total_amount = all_papers.get("total_amount_charged")
            if total_amount:
                cache.set(cache_key_for_total_amount, total_amount, 60 * 24 * 365)
                cache.set(cache_key_for_total_amount_in_words, num2words(total_amount).title(), 60 * 24 * 365)

        return total_amount

    generate_pdf.short_description = "Generate Bill Receipt"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "client_name",
                "address",
                "phone_number",
            ]

        return []

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user

        super(ReceiptInvoiceAdmin, self).save_model(request, obj, form, change)


admin.site.register(ReceiptInvoice, ReceiptInvoiceAdmin)
