import asyncio
import logging
import threading

from asgiref.sync import sync_to_async
from colorama import Fore
from django.conf import settings
from telegram import Bot, ForceReply, Update
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes

from notifications.models import TelegramChat

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


async def send_message(text):
    chats = await sync_to_async(list)(TelegramChat.objects.all())
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    for chat in chats:
        try:
            await bot.send_message(chat_id=chat.chat_id, text=text, parse_mode="HTML")
        except BadRequest as e:
            if "Chat not found" in str(e):
                logger.warning(
                    f"{Fore.YELLOW}Chat {chat.chat_id} seems gone, removing it{Fore.RESET}"
                )
                await sync_to_async(
                    lambda: TelegramChat.objects.get(chat_id=chat.chat_id).delete()
                )()


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When command /start is received"""
    logger.info(
        f"{Fore.GREEN}New chat id: {update.effective_chat.id}, username: {update.effective_user.username}{Fore.RESET}"
    )
    await sync_to_async(
        lambda: TelegramChat.objects.get_or_create(chat_id=update.effective_chat.id)
    )()
    await update.message.reply_html(
        r"You have been subscribed to LockMyTag notifications",
        reply_markup=ForceReply(selective=True),
    )


async def _stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When command /stop is received"""
    logger.info(
        f"{Fore.YELLOW}Removing chat id: {update.effective_chat.id}, username: {update.effective_user.username}{Fore.RESET}"
    )
    await sync_to_async(
        lambda: TelegramChat.objects.filter(chat_id=update.effective_chat.id).delete()
    )()
    await update.message.reply_html(
        r"You have been unsubscribed from LockMyTag notifications. To subscribe again, send /start",
        reply_markup=ForceReply(selective=True),
    )


async def _main():
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", _start))
    application.add_handler(CommandHandler("stop", _stop))

    await application.initialize()
    await application.updater.start_polling()
    await application.start()

    while True:
        await asyncio.sleep(1)


def start_telegram_bot():
    """Starts the telegram receiver in a separate thread"""
    thread = threading.Thread(target=lambda: asyncio.run(_main()), daemon=True)
    thread.start()
