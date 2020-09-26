from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from num2words import num2words

from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.contrib.auth.models import User

# Create your models here.
from kunal_advertising.receipt_invoice.constants import (
    RATE_OF_GST,
    CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS,
    CACHE_KEY_FOR_TOTAL_AMOUNT,
)
from kunal_advertising.receipt_invoice.validators import phone_number_validator


class CreateUpdateAbstractModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReceiptInvoice(CreateUpdateAbstractModel):
    CHOICE_CASH = "cash"
    CHOICE_CHEQUE = "cheque"

    MODE_OF_PAYMENT_CHOICES = (
        (CHOICE_CASH, "Cash"),
        (CHOICE_CHEQUE, "Cheque"),
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Employee who cut the receipt")
    message_sent = models.BooleanField(null=True, help_text="If True, invoice message has been sent.")
    client_name = models.CharField(max_length=200, help_text="Client for which the invoice has been generated")
    phone_number = models.CharField(validators=[phone_number_validator], max_length=32)
    address = models.TextField(help_text="Address of the client", null=True, blank=True)
    bank_name = models.CharField(
        max_length=100, help_text="Name of the bank given by the client", null=True, blank=True
    )
    branch = models.CharField(
        max_length=100, help_text="Branch name for the bank given by the client", null=True, blank=True
    )
    mode_of_payment = models.CharField(
        max_length=10,
        default=CHOICE_CASH,
        choices=MODE_OF_PAYMENT_CHOICES,
        help_text="Mode of payment which client chose to do the payment.",
    )

    def __str__(self):
        return "Receipt ID:{0} Client Name:{1} Created By:{2}".format(
            self.id, self.client_name, self.created_by.first_name
        )

    def save(self, *args, **kwargs):
        cache.delete(CACHE_KEY_FOR_TOTAL_AMOUNT.format(client_id=self.pk))
        cache.delete(CACHE_KEY_FOR_TOTAL_AMOUNT_IN_WORDS.format(client_id=self.pk))

        super(ReceiptInvoice, self).save(*args, **kwargs)


class PaperForAdvertisement(CreateUpdateAbstractModel):
    name = models.CharField(
        max_length=100,
        help_text="Name of the paper in which Advertisement has to be shown",
    )
    caption = models.CharField(
        max_length=100,
        help_text="Name of the paper in which Advertisement has to be shown",
    )
    edition = models.CharField(
        max_length=100,
        help_text="List of editions in which Advertisement has to be shown",
    )
    receipt_invoice = models.ForeignKey(ReceiptInvoice, on_delete=models.PROTECT, related_name="total_papers")
    rate = models.IntegerField(help_text="Rate at which the amount has to be charged")
    extra_lines_or_words = models.IntegerField(help_text="Number of extra lines in this paper.", null=True, blank=True)
    cost_of_one_extra_line_or_word = models.IntegerField(
        help_text="Cost of one extra line or word excluding GST.", null=True, blank=True
    )
    amount_charged = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Amount(in digits) charged to the client for this paper.",
        null=True,
        blank=True,
    )
    amount_charged_in_words = models.CharField(
        max_length=100,
        help_text="Amount(in words) charged to the client for this paper.",
        null=True,
        blank=True,
    )

    def __init__(self, *args, **kwargs):
        super(PaperForAdvertisement, self).__init__(*args, **kwargs)
        self._prev_rate = self.rate
        self._prev_extra_lines_or_words = self.extra_lines_or_words
        self._prev_cost_of_one_extra_line_or_word = self.cost_of_one_extra_line_or_word

    def __str__(self):
        return "PaperForAdvertisement ID:{0} Paper Name:{1} For Client:{2}".format(
            self.id, self.name, self.receipt_invoice.client_name
        )

    def clean(self):
        if self.extra_lines_or_words and not self.cost_of_one_extra_line_or_word:
            raise ValidationError("Please enter the cost of extra line/word.")
        elif not self.extra_lines_or_words and self.cost_of_one_extra_line_or_word:
            raise ValidationError("Please enter the number of extra lines/words.")

        super(PaperForAdvertisement, self).clean()

    def save(self, *args, **kwargs):
        if self.extra_lines_or_words and self.cost_of_one_extra_line_or_word:
            self.calculate_total_amount_charged()
        else:
            self.amount_charged = self.rate
            self.amount_charged_in_words = num2words(self.amount_charged).title()

        self.log_state_change()

        super(PaperForAdvertisement, self).save(*args, **kwargs)

    def log_state_change(self):
        from django.contrib.admin.models import LogEntry, CHANGE

        messages = []
        if self.rate != self._prev_rate:
            messages.append("Previous rate: {0} | Current rate: {1}".format(self._prev_rate, self.rate))

        if self.extra_lines_or_words != self._prev_extra_lines_or_words:
            messages.append(
                "Previous Extra lines or words: {0} | Current  Extra lines or words: {1}".format(
                    self._prev_extra_lines_or_words, self.extra_lines_or_words
                )
            )

        if self.cost_of_one_extra_line_or_word != self._prev_cost_of_one_extra_line_or_word:
            messages.append(
                "Previous Cost of Extra lines or words: {0} | Current Cost of Extra lines or words: {1}".format(
                    self._prev_cost_of_one_extra_line_or_word,
                    self.cost_of_one_extra_line_or_word,
                )
            )

        try:
            for message in messages:
                LogEntry.objects.create(
                    user_id=1,
                    content_type_id=ContentType.objects.get_for_model(
                        self.receipt_invoice, for_concrete_model=False
                    ).pk,
                    object_id=self.id,
                    object_repr=self.name,
                    action_flag=CHANGE,
                    change_message=message,
                )
        except IntegrityError:
            pass

    def calculate_total_amount_charged(self):
        extra_lines_or_words_cost = self.extra_lines_or_words * self.cost_of_one_extra_line_or_word
        self.amount_charged = self.rate + extra_lines_or_words_cost + ((RATE_OF_GST / 100) * extra_lines_or_words_cost)
        self.amount_charged_in_words = num2words(self.amount_charged).title()


class DatesForPaperAdvertisement(models.Model):
    date = models.DateField()
    paper_for_advertisement = models.ForeignKey(
        PaperForAdvertisement, on_delete=models.PROTECT, related_name="all_dates"
    )

    def __str__(self):
        return "DatesForPaperAdvertisement ID:{0} Date For Publication:{1} For Paper:{2}".format(
            self.id, self.date, self.paper_for_advertisement.name
        )

    def save(self, *args, **kwargs):
        if not self.date:
            raise ValidationError("Please Enter the date.")

        super(DatesForPaperAdvertisement, self).save(*args, **kwargs)
