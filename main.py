import asyncio
import schedule
import time
import logging
import re
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import telegram

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "8668281506:AAGsW1WB1Ha1ccNX1nWZHcNjeP2OQcSLj4A")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8678264762")

URL_BASE = "https://www.easycancha.com/book/clubs/924/sports?sportId=1&lang=es-CL&country=CL"

HORA_INICIO          = 18
HORA_FIN             = 19
DURACIONES_ACEPTADAS = [60, 90]
DIAS_VALIDOS         = [0, 1, 2, 3, 4]
FRECUENCIA_MINUTOS   = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
alertas_enviadas = set()

async def enviar_alerta(mensaje: str):
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="HTML")
        log.info("✅ Alerta enviada")
    except Exception as e:
        log.error(f"❌ Error Telegram: {e}")

async def revisar_disponibilidad():
    hoy = datetime.now()
    if hoy.weekday() not in DIAS_VALIDOS:
        log.info("Fin de semana, sin monitoreo")
        return

    log.info("🔍 Revisando disponibilidad...")
    fechas = []
    for delta in range(0, 5):
        fecha = hoy + timedelta(days=delta)
        if fecha.weekday() in DIAS_VALIDOS:
            fechas.append(fecha.strftime("%Y-%m-%d"))
        if len(fechas) >= 3:
            break

    canchas = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        for fecha in fechas:
            try:
                url = f"{URL_BASE}&date={fecha}"
                log.info(f"📅 Revisando: {fecha}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)
                contenido = await page.content()
                horas = list(set(re.findall(r'18:[0-5]\d', contenido)))
                for hora in horas:
                    for dur in DURACIONES_ACEPTADAS:
                        clave = f"{fecha}_{hora}_{dur}min"
                        if clave not in alertas_enviadas:
                            canchas.append({"fecha": fecha, "hora": hora, "duracion": dur, "clave": clave})
            except Exception as e:
                log.error(f"Error en {fecha}: {e}")

        await browser.close()

    vistos = set()
    for c in canchas:
        if c["clave"] not in vistos:
            vistos.add(c["clave"])
            msg = (
                f"🎾 <b>¡CANCHA DISPONIBLE!</b>\n\n"
                f"📅 <b>Fecha:</b> {c['fecha']}\n"
                f"⏰ <b>Hora:</b> {c['hora']}\n"
                f"⏱ <b>Duración:</b> {c['duracion']} min\n\n"
                f"👉 <a href='{URL_BASE}&date={c[\"fecha\"]}'>Reservar ahora</a>\n\n"
                f"⚡ ¡Apúrate!"
            )
            await enviar_alerta(msg)
            alertas_enviadas.add(c["clave"])
            await asyncio.sleep(1)

    if not vistos:
        log.info("Sin canchas disponibles")

def job():
    asyncio.run(revisar_disponibilidad())

async def inicio():
    await enviar_alerta(
        "🤖 <b>Bot Youtopia activo ✅</b>\n\n"
        "Monitoreando canchas de Tenis\n"
        "📅 Lunes a Viernes\n"
        "⏰ 18:00 – 19:00\n"
        f"🔄 Revisando cada {FRECUENCIA_MINUTOS} minutos"
    )

if __name__ == "__main__":
    log.info("Bot Youtopia iniciando...")
    asyncio.run(inicio())
    job()
    schedule.every(FRECUENCIA_MINUTOS).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)
