import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os

# --- CONFIGURACIÓN SEGURA ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ARCHIVO_MEMORIA = 'memoria_pollito.json'

# Diccionario de URLs actualizado (incluyendo las dos de Jaén corregidas)
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

# Filtro inteligente para Derecho y ADE
PALABRAS_CLAVE = [
    "economia", "ade", "empresa", "contabilidad", "finanzas", "comercializacion", 
    "marketing", "organizacion", "derecho", "civil", "penal", "constitucional", 
    "administrativo", "laboral", "mercantil", "procesal", "internacional", 
    "fol", "orientacion laboral", "administracion de empresas", "secundaria", "fp", 
    "interino", "sustituto", "convocatoria", "bolsa", "sipri", "resolucion"
]

def cargar_datos():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, 'r') as f:
            datos = json.load(f)
            # Aseguramos que los enlaces sean sets para comparar
            datos["enlaces"] = {k: set(v) for k, v in datos.get("enlaces", {}).items()}
            return datos
    return {"enlaces": {}, "usuarios": []}

def guardar_datos(datos):
    with open(ARCHIVO_MEMORIA, 'w') as f:
        # Convertimos sets a listas para poder guardarlo en JSON
        datos_para_guardar = {
            "usuarios": datos["usuarios"],
            "enlaces": {k: list(v) for k, v in datos["enlaces"].items()}
        }
        json.dump(datos_para_guardar, f)

def obtener_nuevos_usuarios(usuarios_existentes):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url).json()
        nuevos = []
        if r.get("ok"):
            for update in r["result"]:
                if "message" in update and "text" in update["message"]:
                    user_id = str(update["message"]["chat"]["id"])
                    texto = update["message"]["text"]
                    # Solo registramos si pulsa /start y no lo conocemos ya
                    if texto == "/start" and user_id not in usuarios_existentes:
                        nuevos.append(user_id)
        return nuevos
    except:
        return []

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': texto})

# --- EJECUCIÓN ---
datos = cargar_datos()
hubo_cambios = False

# 1. Pescar nuevos suscriptores (Mangel)
nuevos_ids = obtener_nuevos_usuarios(datos["usuarios"])
for nid in nuevos_ids:
    datos["usuarios"].append(nid)
    hubo_cambios = True
    enviar_mensaje(nid, "🐣 ✨ ¡Hola mi Pollito! ✨ 🐣\n\nTu bot personal ya está activado. Te avisaré por aquí en cuanto salgan plazas de ADE 📊 o Derecho ⚖️.\n\n¡Mucha suerte, tú puedes con todo! 💛")

# 2. Rastrear las webs
for nombre, url in URLS.items():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            sopa = BeautifulSoup(res.text, 'html.parser')
            enlaces_actuales = set()
            
            for a in sopa.find_all('a', href=True):
                link = urljoin(url, a['href'])
                if any(p in link.lower() or p in a.text.lower() for p in PALABRAS_CLAVE):
                    enlaces_actuales.add(link)
            
            if nombre not in datos["enlaces"]:
                datos["enlaces"][nombre] = enlaces_actuales
                hubo_cambios = True
            else:
                nuevos = enlaces_actuales - datos["enlaces"][nombre]
                if nuevos:
                    mensaje = f"🐥 ¡Pío, pío, mi Pollito! ✨\n\n🏛 **Novedades en:** {nombre}\n\n"
                    for n in nuevos:
                        mensaje += f"💛 {n}\n"
                    
                    for uid in datos["usuarios"]:
                        enviar_mensaje(uid, mensaje)
                    
                    datos["enlaces"][nombre] = enlaces_actuales
                    hubo_cambios = True
    except Exception as e:
        print(f"Error en {nombre}: {e}")

# 3. Guardar si hay algo nuevo
if hubo_cambios:
    guardar_datos(datos)