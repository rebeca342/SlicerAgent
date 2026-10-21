from pathlib import Path
import subprocess
import tempfile
import os


SLICER_EXE = Path(r"C:\Users\Usuario\AppData\Local\slicer.org\3D Slicer 5.10.0\Slicer.exe")

SLICER_MODULE_PATH = Path( r"C:\Users\Usuario\Documents\MASTER IA\TFM\ExtensionSlicer\SlicerAgent\SlicerAgent")


def run_functionality_test(
    scene_path: str,
    tool_code: str,
    validator_code: str,
):
    """
    1. Carga la escena
    2. Ejecuta el código del tool
    3. Captura stdout
    4. Ejecuta el código del validador
    5. Imprime stdout
    6. Cierra Slicer

    """

    full_script = f'''
import sys
import io
import contextlib
import slicer

sys.path.append(r"{SLICER_MODULE_PATH}")


# Carga la escena


scene = r"""{scene_path}"""

if scene == "EMPTY_SCENE":

    slicer.mrmlScene.Clear()

else:

    slicer.mrmlScene.Clear()
    slicer.util.loadScene(scene)


# Ejecuta el código del tool


_stdout_buffer = io.StringIO()

tool_code = r"""
{tool_code}
"""

execution_globals = globals()

print("TOOL_START")

with contextlib.redirect_stdout(_stdout_buffer):
    exec(tool_code, execution_globals)

print("TOOL_END")


# Captura stdout


__stdout__ = _stdout_buffer.getvalue()


# Ejecuta el código del validador


validator_code = r"""
{validator_code}
"""

execution_globals["__stdout__"] = __stdout__

print("TOOL_FINISHED")

print("VALIDATOR_START")

try:
    exec(validator_code, execution_globals)
    print("VALIDATOR_FINISHED")
except Exception as e:
    print("VALIDATOR_EXCEPTION:", e)


# Imprime stdout


print(__stdout__)


# Cierra Slicer


slicer.app.exit()
'''

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as f:

        f.write(full_script)
        script_path = f.name

    try:

        print("Launching Slicer process...")

        result = subprocess.run(
            [
                str(SLICER_EXE),
                "--python-script",
                script_path,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        print("Slicer process finished.")

        ignored_error = """RuntimeError: qSlicerScriptedLoadableModule::setPythonSource - Failed to load scripted loadable module: class slicer_helpers was not found in file C:/Users/Usuario/Documents/MASTER IA/TFM/ExtensionSlicer/SlicerChat/SlicerChatModule/slicer_helpers.py
    Fail to instantiate module  "slicer_helpers"
    The following modules failed to be instantiated:
    slicer_helpers
    """

        stderr = result.stderr.replace(
            ignored_error,
            ""
        ).strip()

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": stderr,
        }

    except subprocess.TimeoutExpired:

        print("Slicer timeout!")

        return {
            "success": False,
            "returncode": -999,
            "stdout": "",
            "stderr": "TIMEOUT (180 seconds)",
        }

    finally:

        if os.path.exists(script_path):
            os.remove(script_path)


if __name__ == "__main__":

    tool_code = '''
print("TOOL EXECUTED")
'''

    validator_code = '''
print("VALIDATION_SUCCESS")
'''

    result = run_functionality_test(
        scene_path="EMPTY_SCENE",
        tool_code=tool_code,
        validator_code=validator_code,
    )

    print(result)