from pathlib import Path

# Path del ejecutable de Slicer y del módulo de SlicerAgent

SLICER_EXE = Path(r"C:\Users\Usuario\AppData\Local\slicer.org\3D Slicer 5.10.0\Slicer.exe")

SLICER_MODULE_PATH = Path( r"C:\Users\Usuario\Documents\MASTER IA\TFM\ExtensionSlicer\SlicerAgent\SlicerAgent")

import subprocess
import tempfile
import os

def run_code_in_slicer(code: str):

    # Código completo que ejecutará Slicer
    full_script = f"""
import sys
import slicer

sys.path.append(r"{SLICER_MODULE_PATH}")

{code}

slicer.app.exit()
"""
    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:

        f.write(full_script)
        script_path = f.name

    try:

        result = subprocess.run(
            [
                str(SLICER_EXE),
                "--python-script",
                script_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        stderr = result.stderr

        # Ignorar el warning conocido al iniciar Slicer
        ignored_error = """RuntimeError: qSlicerScriptedLoadableModule::setPythonSource - Failed to load scripted loadable module: class slicer_helpers was not found in file C:/Users/Usuario/Documents/MASTER IA/TFM/ExtensionSlicer/SlicerChat/SlicerChatModule/slicer_helpers.py
Fail to instantiate module  "slicer_helpers"
The following modules failed to be instantiated:
   slicer_helpers
"""

        stderr = stderr.replace(ignored_error, "").strip()

        success = (
            result.returncode == 0
            and stderr == ""
        )

        return {
            "success": success,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    finally:

        if os.path.exists(script_path):
            os.remove(script_path)


if __name__ == "__main__":

    test_code = """
import slicer
from slicer_helpers import test_function

test_function()

print("HELLO FROM SLICER")
"""

    result = run_code_in_slicer(test_code)

    print(result)