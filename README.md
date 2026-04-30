# bot_aya
Bot que chequea interrupción de servicio de Agua del AYA

## Configuración de GitHub Actions

Este repositorio usa un workflow de GitHub Actions que corre cada 15 minutos y ejecuta `bot_aya.py`.

### Pasos

1. En GitHub, ve a `Settings` → `Secrets and variables` → `Actions`.
2. Agrega los siguientes secretos:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. El workflow ya está definido en `.github/workflows/aya-check.yml`.

### Qué hace el workflow

- instala Python 3.12
- instala la dependencia `requests`
- ejecuta `python bot_aya.py`
- usa los secretos para enviar mensajes por Telegram sin exponerlos en el código
- commitea el estado de interrupciones para persistencia entre ejecuciones

### Detección de cambios

El bot solo envía mensajes cuando hay cambios en las interrupciones de agua:

| Caso | Mensaje enviado |
|------|-----------------|
| Nueva interrupción | 🆕 **NUEVA** + detalles |
| Interrupción resuelta | ✅ Notificación de resolución |
| Todas resueltas | ✅ "Se han resuelto todas..." |
| Sin cambios | ❌ No se envía mensaje |

El estado se guarda en `estado_anterior.json` y se commitea en el repositorio para persistencia entre ejecuciones de GitHub Actions.

### Nota

No dejes credenciales hardcodeadas en `bot_aya.py`. Usa siempre los secretos de GitHub Actions para mantener seguro el token y el chat ID.

### Validación local

Puedes verificar localmente que las variables de entorno existen y que `bot_aya.py` no tiene errores de sintaxis ejecutando:

```bash
python validate_env.py
```

### Ejecutar localmente

```bash
python bot_aya.py
```

**Nota**: La primera ejecución guardará el estado sin enviar mensaje. Las siguientes compararán con el estado guardado.

