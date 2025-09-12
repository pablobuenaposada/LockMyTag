from django.contrib import admin

from .models import Lock, TelegramChat


class LockAdmin(admin.ModelAdmin):
    list_display = ("id", "tag", "status", "last_notified")
    readonly_fields = ("last_notified", "created", "modified")
    list_filter = ["tag__name"]


class TelegramChatAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "created")
    readonly_fields = ("created", "modified")


admin.site.register(Lock, LockAdmin)
admin.site.register(TelegramChat, TelegramChatAdmin)
