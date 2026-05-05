import requests
import os
import re
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

# Leemos las credenciales desde los Secretos de GitHub (Variables de entorno)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

URL = 'https://www.aya.go.cr/inicio/gestiones_interes/is/interrupciones_servicio?provincia=1&canton=8&distrito=102'

# Usamos algo un poco más corto por si cambian la redacción en la página
TEXTO_BUSCADO = "agua potable"

ARCHIVO_ESTADO = "estado_anterior.json"


def cargar_estado():
    """Carga el estado anterior desde el archivo JSON."""
    if Path(ARCHIVO_ESTADO).exists():
        try:
            with open(ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar estado: {e}")
    return None


def guardar_estado(ids_interrupciones):
    """Guarda el estado actual en un archivo JSON."""
    estado = {
        "ids": ids_interrupciones,
        "timestamp": datetime.now().isoformat()
    }
    try:
        with open(ARCHIVO_ESTADO, 'w', encoding='utf-8') as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        print(f"Estado guardado: {len(ids_interrupciones)} interrupciones.")
    except Exception as e:
        print(f"Error al guardar estado: {e}") 

def enviar_mensaje_telegram(mensaje):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    if not TOKEN or not CHAT_ID:
        print("Error: TOKEN o CHAT_ID no configurados en las variables de entorno.")
        return

    data = {'chat_id': CHAT_ID, 'text': mensaje}
    try:
        response = requests.post(url_api, data=data)
        response.raise_for_status()
        print(f"Mensaje enviado con éxito: {response.status_code}")
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def obtener_datos_playwright():
    print("Obteniendo datos de interrupciones con Playwright...")
    from playwright.sync_api import sync_playwright
    import re
    
    api_data = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            def handle_response(response):
                nonlocal api_data
                if "SitioWeb/Interrupciones" in response.url and response.status == 200:
                    try:
                        api_data = response.json()
                    except:
                        pass

            page.on("response", handle_response)
            
            page.goto("https://www.aya.go.cr/inicio/gestiones_interes/is/interrupciones_servicio")
            page.wait_for_timeout(3000)
            
            try:
                # Seleccionar Provincia (San José)
                page.locator("p-dropdown").nth(0).click()
                page.wait_for_timeout(1000)
                page.locator("p-dropdownitem").filter(has_text=re.compile(r"SAN JOS", re.IGNORECASE)).first.click()
                page.wait_for_timeout(1000)
                
                # Seleccionar Canton (San José)
                page.locator("p-dropdown").nth(1).click()
                page.wait_for_timeout(1000)
                page.locator("p-dropdownitem").filter(has_text=re.compile(r"SAN JOS", re.IGNORECASE)).first.click()
                page.wait_for_timeout(1000)
                
                # Seleccionar Distrito (San Sebastián)
                page.locator("p-dropdown").nth(2).click()
                page.wait_for_timeout(1000)
                page.locator("p-dropdownitem").filter(has_text=re.compile(r"SAN SEBASTI", re.IGNORECASE)).first.click()
                page.wait_for_timeout(1000)
                
                # Click Consultar
                page.locator("button:has-text('Consultar')").click()
                
                # Esperamos hasta 10 segundos a que la API responda
                for _ in range(10):
                    page.wait_for_timeout(1000)
                    if api_data is not None:
                        break
            except Exception as e:
                print("Error seleccionando opciones en la UI:", e)
            
            browser.close()
    except Exception as e:
        print(f"Error en Playwright: {e}")
        
    return api_data

def revisar_pagina():
    print("Revisando la página del AyA...")
    
    # Cargar estado anterior
    estado_anterior = cargar_estado()
    ids_anteriores = set(estado_anterior.get("ids", [])) if estado_anterior else set()
    
    data = obtener_datos_playwright()
    
    if data is None:
        print("No se pudieron obtener los datos (bloqueo, timeout o error en la UI). Abortando.")
        return

    print("Datos obtenidos exitosamente de la API.")
    
    entidades = data.get("entidad")
    if not entidades:
        print("No se encontraron interrupciones.")
        if ids_anteriores:
            mensaje_resueltas = "✅ Se han resuelto todas las interrupciones de agua potable."
            enviar_mensaje_telegram(mensaje_resueltas)
            guardar_estado([])
        else:
            guardar_estado([])
        return

    interrupciones_agua = [
        item for item in entidades
        if re.search(TEXTO_BUSCADO, str(item.get("descripcion", "")), re.IGNORECASE)
    ]

    if not interrupciones_agua:
        print("No se detectaron interrupciones de agua potable.")
        if ids_anteriores:
            mensaje_resueltas = "✅ Se han resuelto todas las interrupciones de agua potable."
            enviar_mensaje_telegram(mensaje_resueltas)
            guardar_estado([])
        return

    # Obtener IDs actuales
    ids_actuales = {item.get('idInterrupcion') for item in interrupciones_agua}
    
    print(f"Se encontraron {len(interrupciones_agua)} interrupciones de agua potable.")
    
    # Detectar cambios
    nuevas = ids_actuales - ids_anteriores
    resueltas = ids_anteriores - ids_actuales
    
    if not nuevas and not resueltas:
        print("No hay cambios respecto al estado anterior. No se envía mensaje.")
        return
    
    # Construir mensajes según cambios detectados
    mensajes = []
    
    if nuevas:
        for item in interrupciones_agua:
            if item.get('idInterrupcion') in nuevas:
                mensajes.append(
                    f"🆕 NUEVA\nID: {item.get('idInterrupcion')}\nInicio: {item.get('inicioAfectacion')}\nFin: {item.get('finAfectacion')}\nDescripción: {item.get('descripcion')}"
                )
    
    if resueltas:
        mensajes.append(f"✅ Se resolvieron {len(resueltas)} interrupción(es) de agua potable.")
    
    alerta = (
        "¡Alerta! Cambios detectados en el servicio de agua potable en el AyA.\n\n"
        + "\n\n".join(mensajes[:3])
        + f"\n\nRevisa el enlace: {URL}"
    )
    enviar_mensaje_telegram(alerta)
    
    guardar_estado(list(ids_actuales))

if __name__ == "__main__":
    revisar_pagina()