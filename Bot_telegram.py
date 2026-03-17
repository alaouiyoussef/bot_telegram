import json
import os
import asyncio
import subprocess
import sys
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

TOKEN     = "8658834053:AAGV7rg607ukfWJXEseeF_IfrEjYosjqCyw"
CHAT_ID   = "5756054596"
JSON_FILE = "marches.json"
INTERVALLE_HEURES = 6

def charger_marches():
    if not os.path.exists(JSON_FILE):
        print(f"[ERREUR] Fichier {JSON_FILE} introuvable.")
        return []
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def formater_marche(marche, numero):
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f" *Marché #{numero}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f" *Type :* {marche.get('type', 'N/A')}\n"
        f" *Publication :* {marche.get('date_publication', 'N/A')}\n"
        f" *Acheteur :* {marche.get('acheteur', 'N/A')}\n"
        f" *Objet :* {marche.get('objet', 'N/A')}\n"
        f"*Lieu :* {marche.get('lieu', 'N/A')}\n"
        f" *Date limite :* {marche.get('date_limite', 'N/A')}\n"
    )


def lancer_scraper():
    print("[INFO] Lancement du scraper...")
    try:
        subprocess.run([sys.executable, "scraper.py"], timeout=300)
        print("[INFO] Scraper terminé.")
    except subprocess.TimeoutExpired:
        print("[ERREUR] Scraper timeout après 5 minutes.")
    except Exception as e:
        print(f"[ERREUR] Scraper : {e}")


async def envoyer_message(bot, texte):
    try:
        result = await bot.send_message(chat_id=CHAT_ID, text=texte, parse_mode="Markdown")
        print(f"[DEBUG] Message envoyé, message_id={result.message_id}")
    except TelegramError as e:
        print(f"[ERREUR ENVOI] {type(e).__name__}: {e}")
    await asyncio.sleep(1)


async def envoyer_en_lots(bot, marches):
    total      = len(marches)
    maintenant = datetime.now().strftime("%d/%m/%Y à %H:%M")

    intro = (
        f" *Mise à jour des marchés publics*\n"
        f" {maintenant}\n"
        f" *{total} marché(s) trouvé(s)*\n"
        f"─────────────────────────"
    )
    await envoyer_message(bot, intro)

    message = ""
    for i, marche in enumerate(marches, start=1):
        bloc = formater_marche(marche, i)
        if len(message) + len(bloc) > 4000:
            await envoyer_message(bot, message)
            message = ""
        message += bloc + "\n"

    if message:
        await envoyer_message(bot, message)

    await envoyer_message(bot, f" *Envoi terminé — {total} marché(s) affiché(s).*")

async def cycle_complet():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Début du cycle...")

    await asyncio.get_event_loop().run_in_executor(None, lancer_scraper)

    marches = charger_marches()
    bot     = Bot(token=TOKEN)

    if not marches:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=" Aucun marché trouvé ou fichier JSON vide.",
            parse_mode="Markdown"
        )
        return

    try:
        await envoyer_en_lots(bot, marches)
        print(f"[OK] {len(marches)} marché(s) envoyé(s) sur Telegram.")
    except TelegramError as e:
        print(f"[ERREUR Telegram] {e}")


async def main():
    print("═" * 40)
    print("  Bot Telegram — Marchés Publics")
    print("═" * 40)
    print(f"  Envoi toutes les {INTERVALLE_HEURES} heures")
    print(f"  Prochain envoi : maintenant\n")

    while True:
        await cycle_complet()
        print(f"\n[INFO] Prochain cycle dans {INTERVALLE_HEURES}h. En attente...")
        await asyncio.sleep(INTERVALLE_HEURES * 3600)


if __name__ == "__main__":
    asyncio.run(main())