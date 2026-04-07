import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ARCHIVO_MEMORIA = 'memoria_pollito.json'

URLS = {
    "UJA (Jaén - Sustituciones)": "https://www.ujaen.es/servicios/servpod/bolsa-de-sustitucion-pdi",
    "UJA (Jaén - Contratado)": "https://www.ujaen.es/servicios/servpod/tipo-de-plazaoferta/pdi-contratado",
    "SIPRI (Junta - Secundaria/FP)": "https://www.juntadeandalucia.es/educacion/sipri/inicio/",
    "Bolsas Extraordinarias (Junta)": "https://www.juntadeandalucia.es/educacion/portals/web/ced/novedades",
    "UGR (Granada)": "https://serviciopdi.ugr.es/contratado/concursopublico/sustitutointerino/index.html",
    "UCA (Cádiz)": "https://personal.uca.es/convocatorias-de-bolsas-de-psi/",
    "UHU (Huelva)": "https://www.uhu.es/ordenacion-academica/plazas-de-profesorado/plazas-de-profesor-sustituto",
    "US (Sevilla)": "https://recursoshumanos.us.es/index.php?page=pdi/empleo_publico"
}

PALABRAS_CLAVE = ["economia", "ade", "empresa", "contabilidad", "finanzas", "marketing", "derecho", "civil", "penal", "administrativo", "laboral", "mercantil", "fol", "secundaria", "fp", "interino", "sustituto", "convocatoria", "bolsa", "sipri"]

def cargar_datos():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, 'r') as f:
            return json.load(f)
    return {"enlaces": {}, "usuarios": []}

def guardar_datos(datos):
    with open(ARCHIVO_MEMORIA, 'w') as f:
        json.dump(datos, f)

def obtener_nuevos_usuarios(usuarios_existentes):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url).json()
        nuevos = []
        if r.get("ok"):
            for update in r["result"]:
                if "message" in update:
                    user_id = str(update["message"]["chat"]["id"])
                    if user_id not in usuarios_existentes:
                        nuevos.append(user_id)
        return nuevos
    except:
        return []

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': texto})

# --- PROCESO ---
datos = cargar_datos()
hubo_cambios = False

# 1. Buscar si Mangel (o alguien nuevo) ha iniciado el bot
nuevos_ids = obtener_nuevos_usuarios(datos["usuarios"])
for nid in nuevos_ids:
    datos["usuarios"].append(nid)
    hubo_cambios = True
    enviar_mensaje(nid, "🐣 ✨ ¡Hola mi Pollito! ✨ 🐣\n\nTu bot personal ya está activado. Te avisaré aquí de plazas de ADE y Derecho. ¡Te quiero! 💛")

# 2. Revisar las webs
for nombre, url in URLS.items():
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if res.status_code == 200:
            sopa = BeautifulSoup(res.text, 'html.parser')
            enlaces_actuales = []
            for a in sopa.find_all('a', href=True):
                link = urljoin(url, a['href'])
                if any(p in link.lower() or p in a.text.lower() for p in PALABRAS_CLAVE):
                    enlaces_actuales.append(link)
            
            if nombre not in datos["enlaces"]:
                datos["enlaces"][nombre] = enlaces_actuales
                hubo_cambios = True
            else:
                nuevos = set(enlaces_actuales) - set(datos["enlaces"][nombre])
                if nuevos:
                    mensaje = f"🐥 ¡Novedades en {nombre}!\n\n" + "\n".join([f"💛 {l}" for l in nuevos])
                    for uid in datos["usuarios"]:
                        enviar_mensaje(uid, mensaje)
                    datos["enlaces"][nombre] = enlaces_actuales
                    hubo_cambios = True
    except:
        continue

if hubo_cambios:
    guardar_datos(datos)