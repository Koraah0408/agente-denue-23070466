import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.herramientas import cargar_datos, Herramientas
from app.agente import responder
from app.modelo import llamar_modelo

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Global variables loaded once
df, sectores = cargar_datos("data/denue_tampico_madero.csv", "data/sectores_scian.csv")
herramientas = Herramientas(df, sectores)

sistema_path = os.path.join("prompts", "sistema.md")
if os.path.exists(sistema_path):
    with open(sistema_path, "r", encoding="utf-8") as f:
        sistema_prompt = f.read()
else:
    sistema_prompt = "Eres un agente analista del DENUE."


def obtener_whitelist() -> set:
    raw = os.environ.get("TELEGRAM_USUARIOS_PERMITIDOS", "")
    if not raw.strip():
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def es_usuario_autorizado(user_id: int, username: str = None) -> bool:
    whitelist = obtener_whitelist()
    if not whitelist:
        return True

    uid_str = str(user_id)
    if uid_str in whitelist:
        return True
    if username and f"@{username.lstrip('@')}" in whitelist:
        return True
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not es_usuario_autorizado(user_id, username):
        await update.message.reply_text(f"Acceso no autorizado. Tu chat_id es: {user_id}")
        return

    msg = (
        "Hola. Soy el Agente Analista del DENUE (Tampico y Ciudad Madero, datos INEGI 05/2026).\n\n"
        "Hazme cualquier pregunta sobre establecimientos, conteos por actividad, ranking por colonia o sectores económicos."
    )
    await update.message.reply_text(msg)


async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not es_usuario_autorizado(user_id, username):
        await update.message.reply_text(f"Acceso no autorizado. Tu chat_id es: {user_id}")
        return

    msg = (
        "Ejemplos de preguntas:\n"
        "- ¿Cuántas cafeterías hay en Tampico?\n"
        "- ¿Cuáles son las 5 actividades con más establecimientos en Ciudad Madero?\n"
        "- ¿Qué sector económico tiene más establecimientos en Tampico?"
    )
    await update.message.reply_text(msg)


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not es_usuario_autorizado(user_id, username):
        await update.message.reply_text(f"Acceso no autorizado. Tu chat_id es: {user_id}")
        return

    pregunta = update.message.text.strip()
    if not pregunta:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    user_label = f"tg_{user_id}"

    # CRITICAL CONTRACT REQUIREMENT: Run responder in a thread pool using asyncio.to_thread
    try:
        res = await asyncio.to_thread(
            responder,
            pregunta=pregunta,
            herramientas=herramientas,
            sistema=sistema_prompt,
            llamar=llamar_modelo,
            canal="telegram",
            usuario=user_label,
        )

        respuesta_texto = res.get("respuesta", "No se obtuvo respuesta.")
    except Exception as e:
        respuesta_texto = f"Ocurrió un error al procesar tu consulta: {str(e)}"

    # Send long responses in chunks of 4000 chars if necessary
    for i in range(0, len(respuesta_texto), 4000):
        chunk = respuesta_texto[i : i + 4000]
        await update.message.reply_text(chunk)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token or token == "tu_token_de_telegram_aqui":
        print("ERROR: TELEGRAM_BOT_TOKEN no configurado en .env")
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ayuda", ayuda_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("Bot de Telegram iniciado. Presiona Ctrl+C para detener.")
    app.run_polling()


if __name__ == "__main__":
    main()
