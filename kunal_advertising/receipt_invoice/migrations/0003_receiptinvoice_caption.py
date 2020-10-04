# Generated by Django 3.1.1 on 2020-10-04 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("receipt_invoice", "0002_receiptinvoice_message_response"),
    ]

    operations = [
        migrations.AddField(
            model_name="receiptinvoice",
            name="caption",
            field=models.CharField(help_text="Caption for the receipt.", max_length=100, null=True),
        ),
    ]
