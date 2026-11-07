"""Iniciador: instala lo necesario, pide las API keys, prepara los datos y abre el agente.

Se ejecuta con iniciar.bat (Windows) o iniciar.sh (Mac o Linux).
Opciones: --claves vuelve a pedir las API keys; --probar prepara todo, abre y cierra sin navegador.
"""
import getpass
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENV = BASE / ".env"
EJEMPLO = BASE / ".env.example"
MARCA = BASE / ".venv" / "requisitos_instalados.txt"
SIN_CLAVE = "tu_api_key_aqui"
URL = "http://localhost:8501"
PROVEEDORES = {
    "gemini": ("GOOGLE_API_KEY", "Gemini (gratis)", "https://aistudio.google.com/apikey"),
    "claude": ("ANTHROPIC_API_KEY", "Claude (de pago)", "https://console.anthropic.com/settings/keys"),
}


def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


def preguntar(texto: str, oculto: bool = False) -> str:
    """Pide un dato. Las API keys no se muestran en pantalla mientras se pegan."""
    try:
        if oculto and sys.stdin.isatty():
            return getpass.getpass(texto).strip()
        return input(texto).strip()
    except EOFError:
        # Sin nadie que responda, se toma como Enter.
        print()
        return ""


def leer_variable(texto: str, clave: str) -> str:
    encontrado = re.search(rf"^{clave}=(.*)$", texto, re.M)
    return encontrado.group(1).strip() if encontrado else ""


def fijar_variable(texto: str, clave: str, valor: str) -> str:
    """Cambia una línea del .env o la agrega al final."""
    if re.search(rf"^{clave}=", texto, re.M):
        return re.sub(rf"^{clave}=.*$", lambda _: f"{clave}={valor}", texto, flags=re.M)
    return texto.rstrip("\n") + f"\n{clave}={valor}\n"


def tiene_clave(texto: str, variable: str) -> bool:
    valor = leer_variable(texto, variable)
    return bool(valor) and valor != SIN_CLAVE


def revisar_python() -> None:
    if sys.version_info < (3, 10):
        sys.exit("Se necesita Python 3.10 o superior: https://www.python.org/downloads/")
    if len(str(BASE)) > 110:
        print(f"AVISO: la carpeta tiene una ruta larga ({len(str(BASE))} caracteres). Si la instalación "
              "falla, mueve el proyecto a una ruta corta como C:\\dev.")


def instalar_dependencias() -> None:
    titulo("1. Dependencias")
    huella = hashlib.sha256((BASE / "requirements.txt").read_bytes()).hexdigest()
    if MARCA.exists() and MARCA.read_text() == huella:
        print("Ya están instaladas.")
        return
    print("Instalando dependencias. La primera vez puede tardar unos 15 minutos...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=BASE, check=True)
    MARCA.write_text(huella)


def clave_valida(proveedor: str, clave: str) -> bool:
    """Comprueba la key listando modelos: no consume saldo ni cuota de uso."""
    try:
        if proveedor == "claude":
            import anthropic
            anthropic.Anthropic(api_key=clave, base_url="https://api.anthropic.com",
                                timeout=20).models.list(limit=1)
        else:
            from google import genai
            next(iter(genai.Client(api_key=clave).models.list()))
        return True
    except Exception as error:
        print(f"   No se pudo validar: {type(error).__name__}")
        return False


def configurar_claves(volver_a_pedir: bool) -> None:
    titulo("2. API keys")
    if not ENV.exists():
        shutil.copy(EJEMPLO, ENV)
        print("Se creó el archivo .env.")
    texto = ENV.read_text(encoding="utf-8")
    faltan = [p for p, (variable, _, _) in PROVEEDORES.items()
              if volver_a_pedir or not tiene_clave(texto, variable)]
    if not faltan:
        print("Ya están configuradas. Para cambiarlas, ejecuta el iniciador con --claves.")
    else:
        print("El chat puede usar Gemini, Claude o ambos; en el panel eliges el modelo.")
        print("Pega la key y presiona Enter: no se verá en pantalla. Enter sin escribir la omite.")
        print("Sin keys, el chat responde con reglas. Planificar no necesita keys.")
    for proveedor in faltan:
        variable, nombre, enlace = PROVEEDORES[proveedor]
        print(f"\n{nombre}: obtén la key en {enlace}")
        while True:
            clave = preguntar(f"   API key de {nombre}: ", oculto=True)
            if not clave:
                print("   Omitida.")
                break
            if clave_valida(proveedor, clave):
                texto = fijar_variable(texto, variable, clave)
                print("   Guardada en .env.")
                break
            if preguntar("   ¿Intentar de nuevo? (s/n): ").lower() != "s":
                break

    proveedor = leer_variable(texto, "LLM_PROVEEDOR") or "gemini"
    otro = "claude" if proveedor == "gemini" else "gemini"
    if not tiene_clave(texto, PROVEEDORES[proveedor][0]) and tiene_clave(texto, PROVEEDORES[otro][0]):
        texto = fijar_variable(texto, "LLM_PROVEEDOR", otro)

    reales = leer_variable(texto, "FUENTE_DATOS") == "real"
    con_alguna_clave = any(tiene_clave(texto, v) for v, _, _ in PROVEEDORES.values())
    autorizado = leer_variable(texto, "PERMITIR_LLM_CON_DATOS_REALES").lower() == "true"
    if reales and con_alguna_clave and not autorizado:
        print("\nCon datos reales, el chat envía al proveedor nombres de productos, stock y ventas en unidades.")
        if preguntar("¿La empresa autoriza enviar esos datos? (s/n): ").lower() == "s":
            texto = fijar_variable(texto, "PERMITIR_LLM_CON_DATOS_REALES", "true")
    ENV.write_text(texto, encoding="utf-8")


def configuracion() -> dict:
    """Lee la configuración con el Python del proyecto, que ya conoce el .env."""
    codigo = ("from config import settings as s\n"
              "for v in (s.FUENTE_DATOS, s.RUTA_VENTAS, s.RUTA_STOCK, s.DB_PATH, s.CHROMA_DIR): print(v)")
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=BASE, capture_output=True,
                            text=True, encoding="utf-8", check=True).stdout.splitlines()
    return dict(zip(("fuente", "ventas", "stock", "base", "indice"), salida))


def preparar_datos() -> None:
    titulo("3. Datos")
    datos = configuracion()
    if datos["fuente"] == "real":
        faltan = [r for r in (datos["ventas"], datos["stock"]) if not Path(r).exists()]
        if faltan:
            print("No se encontraron los archivos reales:")
            for ruta in faltan:
                print(f"   {ruta}")
            if preguntar("¿Usar los datos simulados del proyecto? (s/n): ").lower() != "s":
                sys.exit("Corrige RUTA_VENTAS y RUTA_STOCK en el archivo .env y vuelve a iniciar.")
            ENV.write_text(fijar_variable(ENV.read_text(encoding="utf-8"), "FUENTE_DATOS", "simulado"),
                           encoding="utf-8")
            datos = configuracion()
    print("Fuente:", "datos reales (solo en este computador)" if datos["fuente"] == "real" else "datos simulados")
    if not Path(datos["base"]).exists():
        print("Cargando datos. Si un Excel está abierto, ciérralo...")
        if subprocess.run([sys.executable, "-m", "scripts.seed_data"], cwd=BASE).returncode:
            sys.exit("No se pudieron cargar los datos.")
    if not Path(datos["indice"]).exists():
        print("Preparando la memoria semántica. La primera vez descarga un modelo...")
        if subprocess.run([sys.executable, "-m", "scripts.index_politicas"], cwd=BASE).returncode:
            sys.exit("No se pudo preparar la memoria semántica.")
    print("Listos.")


def aplicacion_abierta() -> bool:
    try:
        with urllib.request.urlopen(f"{URL}/_stcore/health", timeout=2) as respuesta:
            return respuesta.status == 200
    except OSError:
        return False


def abrir(probar: bool) -> None:
    titulo("4. Agente")
    if aplicacion_abierta():
        print(f"El agente ya estaba abierto en {URL}")
        if not probar:
            webbrowser.open(URL)
        return
    proceso = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
                                "--server.headless", "true"], cwd=BASE)
    print("Abriendo el agente. La primera vez puede tardar cerca de un minuto...")
    for _ in range(180):
        if aplicacion_abierta() or proceso.poll() is not None:
            break
        time.sleep(1)
    if not aplicacion_abierta():
        proceso.terminate()
        sys.exit("El agente no pudo abrirse. Revisa los mensajes de arriba.")
    print(f"Listo: {URL}")
    if probar:
        proceso.terminate()
        proceso.wait()
        print("Prueba terminada.")
        return
    webbrowser.open(URL)
    print("Deja esta ventana abierta mientras usas el agente. Para cerrarlo, presiona Ctrl+C.")
    try:
        proceso.wait()
    except KeyboardInterrupt:
        proceso.terminate()


def main() -> None:
    probar = "--probar" in sys.argv
    print("Agente de reposición de stock")
    revisar_python()
    instalar_dependencias()
    configurar_claves(volver_a_pedir="--claves" in sys.argv)
    preparar_datos()
    abrir(probar)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        sys.exit("La instalación falló. Revisa tu conexión a internet y vuelve a intentarlo.")
    except KeyboardInterrupt:
        print("\nCerrado.")
