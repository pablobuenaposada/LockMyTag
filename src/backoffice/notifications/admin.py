from django.contrib import admin

from notifications.models import TelegramChat


class TelegramChatAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "created")
    readonly_fields = ("created", "modified")


admin.site.register(TelegramChat, TelegramChatAdmin)
