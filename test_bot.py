import asyncio
from telegram import Bot
from telegram.error import TelegramError

TOKEN   = ""
CHAT_ID = ""

async def test():
    try:
        bot  = Bot(token=TOKEN)
        info = await bot.get_me()
        print(f"[OK] Bot connecté : @{info.username}")
        await bot.send_message(chat_id=CHAT_ID, text=" Test réussi ! Le bot fonctionne.")
        print(f"[OK] Message envoyé au chat {CHAT_ID}")
    except TelegramError as e:
        print(f"[ERREUR] {e}")

asyncio.run(test())