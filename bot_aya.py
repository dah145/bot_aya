import requests
import os
import re
import html

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
    
    try:
        response = requests.get(API_URL, params=params, headers=api_headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if not data.get("entidad"):
                print("No se encontraron interrupciones.")
                enviar_mensaje_telegram("Revisión completada. No hay avisos de agua potable en este momento.")
                return

            print(f"Se encontraron {len(data['entidad'])} interrupciones.")
            mensajes = []
            for item in data["entidad"]:
                mensajes.append(
                    f"ID: {item.get('idInterrupcion')}\nInicio: {item.get('inicioAfectacion')}\nFin: {item.get('finAfectacion')}\nDescripción: {item.get('descripcion')}"
                )

            alerta = (
                "¡Alerta! Se detectaron interrupciones en la API del AyA.\n\n"
                + "\n\n".join(mensajes[:3])
                + f"\n\nRevisa el enlace: {URL}"
            )
            enviar_mensaje_telegram(alerta)
        else:
            print(f"Error al acceder a la API. Código: {response.status_code}")
            enviar_mensaje_telegram(f"Error al acceder a la API del AyA. Código: {response.status_code}")

    except Exception as e:
        print(f"Ocurrió un error de conexión: {e}")
        enviar_mensaje_telegram(f"Ocurrió un error de conexión con la API del AyA: {e}")

if __name__ == "__main__":
    revisar_pagina()