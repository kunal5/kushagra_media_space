"""kushagra_media_space URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from kunal_advertising.receipt_invoice import urls as receipt_invoice_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("_nested_admin/", include("nested_admin.urls")),
    path("receipt-invoice/", include(receipt_invoice_urls)),
]

admin.site.site_header = "Kushagra Media Space Admin"
admin.site.site_title = "Kushagra Media Space Portal"
admin.site.index_title = "Welcome to Kushagra Media Space Portal"
