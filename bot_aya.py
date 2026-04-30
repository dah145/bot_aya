import requests
import os
import re
import html
import json
from pathlib import Path
from datetime import datetime

# Leemos las credenciales desde los Secretos de GitHub (Variables de entorno)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

URL = 'https://www.aya.go.cr/inicio/gestiones_interes/is/interrupciones_servicio?provincia=1&canton=8&distrito=102'
API_URL = "https://apigat.aya.go.cr/sitio/api/SitioWeb/Interrupciones"

params = {
    "FkProvincia": 1,
    "FkCanton": 8,
    "FkDistrito": 102,
    "FechaInicio": "",
    "FechaFin": ""
}

api_headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.aya.go.cr/",
    "Origin": "https://www.aya.go.cr"
}

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

def revisar_pagina():
    print("Revisando la API del AyA...")
    
    # Cargar estado anterior
    estado_anterior = cargar_estado()
    ids_anteriores = set(estado_anterior.get("ids", [])) if estado_anterior else set()
    
    try:
        response = requests.get(API_URL, params=params, headers=api_headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            entidades = data.get("entidad")
            if not entidades:
                print("No se encontraron interrupciones.")
                # Guardar estado vacío si no hay interrupciones
                if not ids_anteriores:
                    guardar_estado([])
                return

            interrupciones_agua = [
                item for item in entidades
                if re.search(TEXTO_BUSCADO, str(item.get("descripcion", "")), re.IGNORECASE)
            ]

            if not interrupciones_agua:
                print("No se detectaron interrupciones de agua potable.")
                # Si había interrupciones antes y ahora no hay, informar que se resolvieron
                if ids_anteriores:
                    mensaje_resueltas = "✅ Se han resuelto todas las interrupciones de agua potable."
                    enviar_mensaje_telegram(mensaje_resueltas)
                    guardar_estado([])
                return

            # Obtener IDs actuales
            ids_actuales = {item.get('idInterrupcion') for item in interrupciones_agua}
            
            print(f"Se encontraron {len(interrupciones_agua)} interrupciones de agua potable.")
            
            # Caso inicial: primera ejecución sin estado previo
            if not ids_anteriores:
                print("Primera ejecución: guardando estado sin enviar mensaje.")
                guardar_estado(list(ids_actuales))
                return
            
            # Detectar cambios
            nuevas = ids_actuales - ids_anteriores
            resueltas = ids_anteriores - ids_actuales
            
            # Si no hay cambios, salir sin enviar mensaje
            if not nuevas and not resueltas:
                print("No hay cambios respecto al estado anterior. No se envía mensaje.")
                return
            
            # Construir mensajes según cambios detectados
            mensajes = []
            
            # Información de interrupciones nuevas
            if nuevas:
                for item in interrupciones_agua:
                    if item.get('idInterrupcion') in nuevas:
                        mensajes.append(
                            f"🆕 NUEVA\nID: {item.get('idInterrupcion')}\nInicio: {item.get('inicioAfectacion')}\nFin: {item.get('finAfectacion')}\nDescripción: {item.get('descripcion')}"
                        )
            
            # Información de interrupciones resueltas
            if resueltas:
                mensajes.append(f"✅ Se resolvieron {len(resueltas)} interrupción(es) de agua potable.")
            
            # Limitar a 3 mensajes nuevos máximo
            alerta = (
                "¡Alerta! Cambios detectados en el servicio de agua potable en la API del AyA.\n\n"
                + "\n\n".join(mensajes[:3])
                + f"\n\nRevisa el enlace: {URL}"
            )
            enviar_mensaje_telegram(alerta)
            
            # Guardar nuevo estado
            guardar_estado(list(ids_actuales))
            
        else:
            error_text = f"Error al acceder a la API del AyA. Código: {response.status_code}"
            print(error_text)
            enviar_mensaje_telegram(error_text)

    except Exception as e:
        error_text = f"Ocurrió un error de conexión con la API del AyA: {e}"
        print(error_text)
        enviar_mensaje_telegram(error_text)

if __name__ == "__main__":
    revisar_pagina()