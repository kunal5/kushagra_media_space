from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User


class UserFilter(SimpleListFilter):
    title = _("Employee")

    parameter_name = "created_by"

    def lookups(self, request, model_admin):
        return [
            (user_id, user_first_name + " " + user_last_name)
            for user_id, user_first_name, user_last_name in User.objects.all()
            .values_list("id", "first_name", "last_name")
            .order_by("first_name")
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by_id=self.value())
