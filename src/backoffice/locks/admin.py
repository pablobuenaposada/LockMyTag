from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from .models import Lock, LockSchedule


class LockScheduleInlineForm(forms.ModelForm):
    class Meta:
        model = LockSchedule
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].initial = "00:00:00"
        self.fields["end_time"].initial = "23:59:59"


class LockScheduleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        schedules_by_day = {}
        for form in self.forms:
            if form.cleaned_data.get("DELETE", False):
                continue
            day = form.cleaned_data.get("day")
            start_time = form.cleaned_data.get("start_time")
            end_time = form.cleaned_data.get("end_time")
            if day is None or start_time is None or end_time is None:
                continue
            if start_time >= end_time:
                raise ValidationError("Start time must be before end time")
            if day not in schedules_by_day:
                schedules_by_day[day] = []
            for other_start, other_end in schedules_by_day[day]:
                if start_time < other_end and end_time > other_start:
                    raise ValidationError(
                        f"Schedule for {dict(LockSchedule.DAYS_OF_WEEK).get(day, day)} overlaps with another schedule for the same day"
                    )
            schedules_by_day[day].append((start_time, end_time))


class LockScheduleInline(admin.TabularInline):
    model = LockSchedule
    extra = 0
    form = LockScheduleInlineForm
    formset = LockScheduleInlineFormSet
    ordering = ("day", "start_time")


class LockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tag__name",
        "colored_status",
        "radius",
        "latitude",
        "longitude",
    )
    readonly_fields = ("created", "modified")
    list_filter = ["tag__name"]
    inlines = [LockScheduleInline]

    def get_inline_instances(self, request, obj=None):
        # only show inlines if editing an existing lock
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def colored_status(self, obj):
        color = "green" if obj.status == "active" else "red"
        return format_html('<span style="color: {};">{}</span>', color, obj.status)

    colored_status.admin_order_field = "status"
    colored_status.short_description = "Status"


admin.site.register(Lock, LockAdmin)
