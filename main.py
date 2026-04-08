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
    "SIPRI (Junta)": "https://www.juntadeandalucia.es/educacion/sipri/inicio/",
    "Novedades Junta (Bolsas)": "https://www.juntadeandalucia.es/educacion/portals/web/ced/novedades",
    "UGR (Granada)": "https://serviciopdi.ugr.es/contratado/concursopublico/sustitutointerino/index.html",
    "UCA (Cádiz)": "https://personal.uca.es/convocatorias-de-bolsas-de-psi/",
    "UHU (Huelva)": "https://www.uhu.es/ordenacion-academica/plazas-de-profesorado/plazas-de-profesor-sustituto",
    "US (Sevilla)": "https://recursoshumanos.us.es/index.php?page=pdi/empleo_publico"
}

PALABRAS_CLAVE = ["economia", "ade", "empresa", "contabilidad", "finanzas", "marketing", "derecho", "civil", "penal", "administrativo", "laboral", "mercantil", "fol", "secundaria", "fp", "interino", "sustituto", "convocatoria", "bolsa", "sipri"]

def cargar_datos():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, 'r') as f:
                d = json.load(f)
                d["enlaces"] = {k: set(v) for k, v in d.get("enlaces", {}).items()}
                if "usuarios" not in d: d["usuarios"] = []
                return d
        except:
            return {"enlaces": {}, "usuarios": []}
    return {"enlaces": {}, "usuarios": []}

def guardar_datos(datos):
    with open(ARCHIVO_MEMORIA, 'w') as f:
        json.dump({"usuarios": datos["usuarios"], "enlaces": {k: list(v) for k, v in datos["enlaces"].items()}}, f)

def obtener_nuevos_usuarios(usuarios_existentes):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    nuevos = []
    try:
        r = requests.get(url).json()
        if r.get("ok"):
            for u in r["result"]:
                if "message" in u and "text" in u["message"]:
                    uid = str(u["message"]["chat"]["id"])
                    if u["message"]["text"] == "/start" and uid not in usuarios_existentes:
                        nuevos.append(uid)
        return nuevos
    except: return []

def enviar_mensaje(chat_id, texto):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'})

# --- LÓGICA ---
datos = cargar_datos()
hubo_cambios = False

# Registro automático de Mangel
nuevos = obtener_nuevos_usuarios(datos["usuarios"])
for n in nuevos:
    datos["usuarios"].append(n)
    hubo_cambios = True
    enviar_mensaje(n, "🐣 *¡Hola mi Pollito!* ✨\n\nTu bot personal ya está activado. Vigilando plazas de *ADE* 📊 y *Derecho* ⚖️ las 24h.\n\n¡Tú puedes con todo! 💛")

# Rastreo de plazas
for nombre, url in URLS.items():
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        sopa = BeautifulSoup(res.text, 'html.parser')
        enlaces_encontrados = set()
        for a in sopa.find_all('a', href=True):
            link = urljoin(url, a['href'])
            if any(p in link.lower() or p in a.text.lower() for p in PALABRAS_CLAVE):
                enlaces_encontrados.add(link)
        
        if nombre not in datos["enlaces"]:
            datos["enlaces"][nombre] = enlaces_encontrados
            hubo_cambios = True
        else:
            nuevos_links = enlaces_encontrados - datos["enlaces"][nombre]
            if nuevos_links:
                msg = f"🐥 *¡Pío pío! Novedades en {nombre}* ✨\n\n" + "\n".join([f"💛 [Enlace]({l})" for l in list(nuevos_links)[:5]])
                for u in datos["usuarios"]: enviar_mensaje(u, msg)
                datos["enlaces"][nombre] = enlaces_encontrados
                hubo_cambios = True
    except: continue

if hubo_cambios: guardar_datos(datos)
