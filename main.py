import asyncio, schedule, time, logging, re, os
from datetime import datetime, timedelta
import requests, telegram

TELEGRAM_TOKEN   = "8668281506:AAGsW1WB1Ha1ccNX1nWZHcNjeP2OQcSLj4A"
TELEGRAM_CHAT_ID = "8678264762"
DIAS_VALIDOS     = [0,1,2,3,4]
FRECUENCIA       = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)
alertas_enviadas = set()

async def enviar(msg):
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="HTML")
        log.info("Alerta enviada")
    except Exception as e:
        log.error(f"Error Telegram: {e}")

async def revisar():
    if datetime.now().weekday() not in DIAS_VALIDOS:
        return
    log.info("Revisando...")
    fechas = []
    for d in range(5):
        f = datetime.now() + timedelta(days=d)
        if f.weekday() in DIAS_VALIDOS:
            fechas.append(f.strftime("%Y-%m-%d"))
        if len(fechas) >= 3:
            break
    for fecha in fechas:
        try:
            url = f"https://www.easycancha.com/book/clubs/924/sports?sportId=1&lang=es-CL&country=CL&date={fecha}"
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            horas = list(set(re.findall(r'18:[0-5]\d', r.text)))
            for hora in horas:
                for dur in [60, 90]:
                    clave = f"{fecha}_{hora}_{dur}"
                    if clave not in alertas_enviadas:
                        msg = (f"🎾 <b>CANCHA DISPONIBLE</b>\n"
                               f"📅 {fecha}\n⏰ {hora}\n⏱ {dur} min\n"
                               f"👉 <a href='{url}'>Reservar</a>")
                        await enviar(msg)
                        alertas_enviadas.add(clave)
        except Exception as e:
            log.error(f"Error {fecha}: {e}")

def job():
    asyncio.run(revisar())

async def inicio():
    await enviar("🤖 <b>Bot Youtopia activo ✅</b>\nLunes-Viernes 18:00-19:00")

if __name__ == "__main__":
    asyncio.run(inicio())
    job()
    schedule.every(FRECUENCIA).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)
