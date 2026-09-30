import argparse
import asyncio
import hashlib
import logging
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()


def leer_permitidos(texto: str) -> set:
    if not texto or not str(texto).strip():
        return set()
    ids = set()
    for item in str(texto).split(","):
        item = item.strip()
        if item.isdigit():
            ids.add(int(item))
    return ids


def partir_mensaje(texto: str, limite: int = 4096) -> list:
    if texto is None:
        return [""]
    if limite < 1:
        limite = 4096
    if len(texto) <= limite:
        return [texto]
    partes = []
    resto = texto
    while resto:
        if len(resto) <= limite:
            partes.append(resto)
            break
        corte = resto.rfind("\n", 0, limite)
        if corte <= 0:
            corte = limite
        partes.append(resto[:corte])
        resto = resto[corte:].lstrip("\n")
    return partes


def usuario_anonimo(identificador) -> str:
    return hashlib.sha256(str(identificador).encode("utf-8")).hexdigest()[:10]


def _sistema():
    ruta = os.path.join("prompts", "sistema.md")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    return "Eres un agente analista del DENUE."


async def con_escribiendo(chat, funcion, *args):
    from telegram.constants import ChatAction

    tarea = asyncio.ensure_future(asyncio.to_thread(funcion, *args))
    while not tarea.done():
        await chat.send_action(ChatAction.TYPING)
        await asyncio.wait([tarea], timeout=4)
    return tarea.result()


def main():
    parser = argparse.ArgumentParser(description="Bot de Telegram del agente DENUE")
    parser.add_argument("--simulado", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token or token.startswith("tu_"):
        print("ERROR: TELEGRAM_BOT_TOKEN no configurado en .env")
        sys.exit(1)

    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

    from app.agente import responder
    from app.herramientas import Herramientas, cargar_datos

    if args.simulado:
        from app.modelo_simulado import llamar_modelo, reset_simulado

        reset_simulado()
        modelo_nombre = "simulado"
    else:
        from app.modelo import llamar_modelo

        modelo_nombre = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    df, sectores = cargar_datos("data/denue_tampico_madero.csv", "data/sectores_scian.csv")
    herramientas = Herramientas(df, sectores)
    sistema = _sistema()
    permitidos = leer_permitidos(os.environ.get("TELEGRAM_USUARIOS_PERMITIDOS", ""))
    contador = {"n": 0}

    os.makedirs("logs", exist_ok=True)
    fecha_str = time.strftime("%Y%m%d-%H%M%S")
    bitacora_path = os.path.join("logs", f"corrida-{fecha_str}.jsonl")

    def id_bitacora():
        contador["n"] += 1
        return "TG-%d" % contador["n"]

    async def rechazar(update: Update):
        uid = update.effective_user.id
        await update.effective_message.reply_text(
            "Este bot es privado. Tu identificador numérico es: %s" % uid
        )

    async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in permitidos:
            await rechazar(update)
            return
        await update.effective_message.reply_text(
            "Puedo responder sobre establecimientos de Tampico y Ciudad Madero "
            "con el DENUE 05/2026 del INEGI: conteos, rankings y listados.\n\n"
            "El DENUE no tiene número exacto de empleados, ventas, ganancias, "
            "salarios ni opiniones.\n\n"
            "Una respuesta puede tardar varios segundos.\n\n"
            "Aviso de privacidad: no escribas datos personales. Los mensajes "
            "pasan por Telegram y por Google."
        )

    async def fuente(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in permitidos:
            await rechazar(update)
            return
        await update.effective_message.reply_text(
            "Fuente: DENUE 05/2026, INEGI. Recorte: municipios de Tampico y Ciudad Madero, Tamaulipas."
        )

    async def pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in permitidos:
            await rechazar(update)
            return
        texto = (update.effective_message.text or "").strip()
        if not texto:
            return
        request_id = id_bitacora()
        try:
            fin = await con_escribiendo(
                update.effective_chat,
                responder,
                texto,
                herramientas,
                sistema,
                llamar_modelo,
                bitacora_path,
                request_id,
                "telegram",
                usuario_anonimo(uid),
                modelo_nombre,
            )
            respuesta_texto = fin.get("respuesta", "No se obtuvo respuesta.")
        except Exception as exc:
            # Mantener el mensaje de Telegram amable, pero dejar el diagnóstico
            # en la consola para poder corregir autenticación, cuota o red.
            logging.exception("Falló la consulta de Telegram (%s): %s", type(exc).__name__, exc)
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                respuesta_texto = (
                    "La cuota temporal de Gemini está agotada. "
                    "Espera a que se restablezca o configura otro modelo/proyecto con cuota disponible."
                )
            else:
                respuesta_texto = (
                    "No pude completar la consulta en este momento. Inténtalo de nuevo en unos minutos."
                )
            corrida_name = os.path.basename(bitacora_path).replace(".jsonl", "").replace("corrida-", "")
            with open(bitacora_path, "a", encoding="utf-8") as f:
                f.write(
                    json_dumps_error(request_id, corrida_name, modelo_nombre)
                )
        for trozo in partir_mensaje(respuesta_texto):
            if trozo:
                await update.effective_message.reply_text(trozo)

    app = ApplicationBuilder().token(token).build()
    app.bot_data["herramientas"] = herramientas
    app.add_handler(CommandHandler("start", inicio))
    app.add_handler(CommandHandler("fuente", fuente))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pregunta))
    print("Bot de Telegram iniciado. Presiona Ctrl+C para detener.")
    app.run_polling()


def json_dumps_error(pid, corrida, modelo):
    import json

    ev = {
        "id": pid,
        "evento": "error",
        "error": "fallo al obtener respuesta del modelo",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "corrida": corrida,
        "modelo": modelo,
    }
    return json.dumps(ev, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    main()
