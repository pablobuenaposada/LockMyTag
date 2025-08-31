from django.contrib import admin

from .models import Tag, TagLocation


class TagAdmin(admin.ModelAdmin):
    exclude = ("id",)
    readonly_fields = ("created", "modified")
    list_display = ("id", "name")


class TagLocationAdmin(admin.ModelAdmin):
    readonly_fields = ("created", "modified")
    list_display = ("hash", "tag__name", "latitude", "longitude", "timestamp")


admin.site.register(Tag, TagAdmin)
admin.site.register(TagLocation, TagLocationAdmin)
