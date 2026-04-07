import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os

# --- CONFIGURACIÓN ---
TOKEN = '8799696387:AAERU_mzdPlxuE1eYf69__4KdeEPipRMdYw'
CHAT_ID = '5477918584'
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

PALABRAS_CLAVE = [
    "economia", "ade", "empresa", "contabilidad", "finanzas", "comercializacion", 
    "marketing", "organizacion", "cuantitativos",
    "derecho", "civil", "penal", "constitucional", "administrativo", "laboral", 
    "mercantil", "procesal", "internacional", "romano",
    "fol", "orientacion laboral", "administracion de empresas", "procesos comerciales",
    "secundaria", "fp", "profesor", "interino", "sustituto",
    "convocatoria", "resolucion", "adjudicacion", "bolsa", "sipri", "listado", "anexo"
]

def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, 'r') as f:
            datos = json.load(f)
            return {k: set(v) for k, v in datos.items()}
    return {}

def guardar_memoria(memoria):
    with open(ARCHIVO_MEMORIA, 'w') as f:
        datos = {k: list(v) for k, v in memoria.items()}
        json.dump(datos, f)

def enviar_mensaje(texto):
    url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    datos = {'chat_id': CHAT_ID, 'text': texto}
    requests.post(url_telegram, data=datos)

# Cargamos la libreta de memoria
enlaces_anteriores = cargar_memoria()
hubo_cambios = False

print("🐥 Despertando al bot Pollito...")

for nombre, url in URLS.items():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(url, headers=headers, timeout=15)
        
        if respuesta.status_code == 200:
            sopa = BeautifulSoup(respuesta.text, 'html.parser')
            enlaces_actuales = set()
            
            for etiqueta_a in sopa.find_all('a', href=True):
                enlace_completo = urljoin(url, etiqueta_a['href'])
                texto_enlace = etiqueta_a.text.lower()
                url_enlace = enlace_completo.lower()
                
                if any(palabra in texto_enlace or palabra in url_enlace for palabra in PALABRAS_CLAVE):
                    enlaces_actuales.add(enlace_completo)
            
            # Si es la primera vez que revisa esta web
            if nombre not in enlaces_anteriores:
                enlaces_anteriores[nombre] = enlaces_actuales
                hubo_cambios = True
                print(f"[{nombre}] Primera revisión. Guardando base de datos.")
            else:
                enlaces_nuevos = enlaces_actuales - enlaces_anteriores[nombre]
                
                if enlaces_nuevos:
                    if len(enlaces_nuevos) <= 10:
                        mensaje = f"🐥 ¡Pío, pío, mi Pollito! ✨\n\n🏛 **Novedades en:** {nombre}\n⚖️📊 He encontrado cositas de ADE/Derecho:\n\n"
                        for nuevo_link in enlaces_nuevos:
                            mensaje += f"💛 {nuevo_link}\n"
                        mensaje += "\n¡Mucha suerte, tú puedes con todo! 💪🏼🥰"
                    else:
                        mensaje = f"🐣 ¡Madre mía, Pollito! Hay una actualización ENORME en {nombre}. 🤯\n\nRevisa la web: {url}\n\n¡A por tu plaza! 🍀"
                    
                    enviar_mensaje(mensaje)
                    enlaces_anteriores[nombre] = enlaces_actuales
                    hubo_cambios = True
                    print(f"[{nombre}] ¡Novedades enviadas!")
                else:
                    print(f"[{nombre}] Todo tranquilo.")
        else:
            print(f"[{nombre}] Error {respuesta.status_code}")
            
    except Exception as e:
        print(f"Error en {nombre}: {e}")

# Si ha habido cambios, guardamos la libreta antes de dormir
if hubo_cambios:
    guardar_memoria(enlaces_anteriores)
    print("Memoria guardada correctamente.")

print("Bot Pollito vuelve a dormirse. Zzz...")