import os
import subprocess
import sys

required = ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]
missing = [name for name in required if not os.environ.get(name)]

if missing:
    print("ERROR: Faltan estas variables de entorno:")
    for name in missing:
        print(f"  - {name}")
    print("\nDefinelas antes de ejecutar el bot o el workflow.")
    print("Ejemplo en PowerShell:")
    print("  $env:TELEGRAM_TOKEN = 'tu_token'")
    print("  $env:TELEGRAM_CHAT_ID = 'tu_chat_id'")
    print("  python validate_env.py")
    sys.exit(1)

print("OK: todas las variables de entorno están definidas.")

try:
    subprocess.run([sys.executable, "-m", "py_compile", "bot_aya.py"], check=True)
    print("OK: bot_aya.py es sintácticamente válido.")
except subprocess.CalledProcessError:
    print("ERROR: bot_aya.py tiene errores de sintaxis.")
    sys.exit(1)

print("\nListo. Ahora puedes ejecutar el bot localmente con:")
print("  python bot_aya.py")
