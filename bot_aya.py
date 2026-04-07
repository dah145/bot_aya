import requests
import os

# Leemos las credenciales desde los Secretos de GitHub (Variables de entorno)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

URL = 'https://www.aya.go.cr/inicio/gestiones_interes/is/interrupciones_servicio?provincia=1&canton=8&distrito=102'
# Usamos algo un poco más corto por si cambian la redacción en la página
TEXTO_BUSCADO = "interrupción del servicio" 

def enviar_mensaje_telegram(mensaje):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': mensaje}
    try:
        requests.post(url_api, data=data)
        print("Mensaje de alerta enviado por Telegram.")
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def revisar_pagina():
    print("Revisando la página del AyA...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            html = response.text.lower()
            
            if TEXTO_BUSCADO.lower() in html:
                alerta = f"¡Alerta! Se detectó un aviso de '{TEXTO_BUSCADO}' en la página del AyA.\n\nRevisa el enlace: {URL}"
                enviar_mensaje_telegram(alerta)
            else:
                print("Revisión completada. No hay avisos en este momento.")
        else:
            print(f"Error al acceder. Código: {response.status_code}")
            
    except Exception as e:
        print(f"Ocurrió un error de conexión: {e}")

if __name__ == "__main__":
    revisar_pagina()