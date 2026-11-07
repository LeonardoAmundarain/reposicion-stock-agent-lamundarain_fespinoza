#!/usr/bin/env bash
# Instala, configura y abre el agente en Mac o Linux. Para volver a ingresar las keys: ./iniciar.sh --claves
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Creando el entorno de Python..."
  python3 -m venv .venv || { echo "Se necesita Python 3.10 o superior: https://www.python.org/downloads/"; exit 1; }
fi
exec .venv/bin/python scripts/iniciar.py "$@"
