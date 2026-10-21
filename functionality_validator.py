"""
functionality_validator.py

Genera código de validación en Python.

"""


import json




def _success(message: str) -> str:
    return f'print("VALIDATION_SUCCESS: {message}")'


def _failure(message: str) -> str:
    return f'raise Exception("VALIDATION_FAILED: {message}")'



# CT WINDOW


def validate_ct_window(validation: dict) -> str:
    """
    Valida que una ventana CT tenga los valores esperados.

    """

    node = validation["node"]
    expected_window = validation["window"]
    expected_level = validation["level"]

    return f'''
import slicer

volume = slicer.util.getNode("{node}")

display = volume.GetDisplayNode()

if display is None:
    raise Exception("VALIDATION_FAILED: Display node not found.")

window = display.GetWindow()
level = display.GetLevel()

if abs(window - {expected_window}) > 0.001:
    raise Exception(
        f"VALIDATION_FAILED: Window expected {expected_window} but got {{window}}"
    )

if abs(level - {expected_level}) > 0.001:
    raise Exception(
        f"VALIDATION_FAILED: Level expected {expected_level} but got {{level}}"
    )

print("VALIDATION_SUCCESS: CT window preset correctly applied.")
'''
    
    

# NODE EXISTS VALIDACION


def validate_node_exists(validation: dict) -> str:
    """
    Valida que un nodo exista y tenga la clase esperada.

    """

    node_name = validation["node"]
    expected_class = validation["class"]

    return f'''
import slicer

try:

    node = slicer.util.getNode("{node_name}")

except Exception:

    raise Exception(
        "VALIDATION_FAILED: Node '{node_name}' was not found."
    )

if node is None:

    raise Exception(
        "VALIDATION_FAILED: Node '{node_name}' does not exist."
    )

actual_class = node.GetClassName()

if actual_class != "{expected_class}":

    raise Exception(
        f"VALIDATION_FAILED: Expected class {expected_class} but got {{actual_class}}"
    )

print("VALIDATION_SUCCESS: Node exists.")
print("Node:", node.GetName())
print("Class:", actual_class)
'''


# SEGMENTATION 3D


def validate_segmentation_3d_visible(validation: dict) -> str:
    """
    Valida que una segmentación sea visible en 3D.

    """

    segmentation_name = validation["segmentation_name"]

    return f'''
import slicer

try:

    segmentation = slicer.util.getNode("{segmentation_name}")

except Exception:

    raise Exception(
        "VALIDATION_FAILED: Segmentation '{segmentation_name}' not found."
    )

displayNode = segmentation.GetDisplayNode()

if displayNode is None:
    raise Exception(
        "VALIDATION_FAILED: Display node not found."
    )

if not displayNode.GetVisibility3D():

    raise Exception(
        "VALIDATION_FAILED: Segmentation is not visible in 3D."
    )

print("VALIDATION_SUCCESS: Segmentation visible in 3D.")
'''


# FILE EXISTS VALIDACION


def validate_file_exists(validation: dict) -> str:
    """
    Valida que un archivo exista y no esté vacío.

    """

    path = validation["path"]

    return f'''
import os

path = r"{path}"

if not os.path.exists(path):

    raise Exception(
        "VALIDATION_FAILED: Output file was not created."
    )

if os.path.getsize(path) == 0:

    raise Exception(
        "VALIDATION_FAILED: Output file is empty."
    )

print("VALIDATION_SUCCESS: File created.")
print(path)
'''


# SCENE SAVED VALIDACION


def validate_scene_saved(validation: dict) -> str:
    """
    Validation for save_scene_as_mrb(file_path)

    {
        "type":"scene_saved",
        "path":"C:/Scenes/Test.mrb"
    }
    """

    path = validation["path"]

    return f'''
import os

scenePath = r"{path}"

if not os.path.exists(scenePath):

    raise Exception(
        "VALIDATION_FAILED: Scene file was not created."
    )

if os.path.getsize(scenePath) == 0:

    raise Exception(
        "VALIDATION_FAILED: Scene file is empty."
    )

print("VALIDATION_SUCCESS: Scene saved.")
print(scenePath)
'''


# SCENE SAVED IN DIRECTORY


def validate_scene_saved_in_directory(validation: dict) -> str:
    """
    Validation for save_scene_as_mrb("directorio")

    """

    directory = validation["directory"]

    return f'''
import os
import glob

directory = r"{directory}"

files = glob.glob(
    os.path.join(directory, "*.mrb")
)

if len(files) == 0:

    raise Exception(
        "VALIDATION_FAILED: No MRB file found inside directory."
    )

latest = max(files, key=os.path.getmtime)

if os.path.getsize(latest) == 0:

    raise Exception(
        "VALIDATION_FAILED: Saved MRB file is empty."
    )

print("VALIDATION_SUCCESS: Scene saved inside directory.")
print(latest)
'''


# SCENE SAVED IN TEMP DIRECTORY


def validate_scene_saved_in_temp_directory(validation: dict) -> str:
    """
    Validation for save_scene_as_mrb("temp_directory")

    """

    return '''
import os
import glob
import slicer

tempDir = slicer.app.temporaryPath

files = glob.glob(
    os.path.join(tempDir, "*.mrb")
)

if len(files) == 0:

    raise Exception(
        "VALIDATION_FAILED: No MRB file found inside temporary directory."
    )

latest = max(files, key=os.path.getmtime)

if os.path.getsize(latest) == 0:

    raise Exception(
        "VALIDATION_FAILED: Temporary MRB file is empty."
    )

print("VALIDATION_SUCCESS: Scene saved in temporary directory.")
print(latest)
'''


# ERROR MESSAGE VALIDACION


def validate_error_message(validation: dict) -> str:
    """
    Valida que se haya producido un mensaje de error esperado.

    """

    expected = validation["contains"].replace("\\", "\\\\")

    return f'''
expected = "{expected}"

if expected not in __stdout__:

    raise Exception(
        "VALIDATION_FAILED: Expected error message not found."
    )

print("VALIDATION_SUCCESS: Error message detected.")
'''


# WARNING MESSAGE VALIDACION


def validate_warning_message(validation: dict) -> str:
    """
    Validate that the expected warning message was produced.

    Example
    -------
    {
        "type": "warning_message",
        "warning_contains": "Possible unsupported file extension"
    }
    """

    expected = validation["warning_contains"].replace("\\", "\\\\")

    return f'''
expected = "{expected}"

if expected not in __stdout__:

    raise Exception(
        "VALIDATION_FAILED: Expected warning message not found."
    )

print("VALIDATION_SUCCESS: Warning message detected.")
'''



# VALIDADOR DISPATCHER


def get_validator_code(validation: dict) -> str:
    """
    Devuelve el código de validación correspondiente al tipo de validación especificado.
    
    """

    validation_type = validation["type"]

    if validation_type == "ct_window":
        return validate_ct_window(validation)

    elif validation_type == "node_exists":
        return validate_node_exists(validation)

    elif validation_type == "segmentation_3d_visible":
        return validate_segmentation_3d_visible(validation)

    elif validation_type == "file_exists":
        return validate_file_exists(validation)

    elif validation_type == "scene_saved":
        return validate_scene_saved(validation)

    elif validation_type == "scene_saved_in_directory":
        return validate_scene_saved_in_directory(validation)

    elif validation_type == "scene_saved_in_temp_directory":
        return validate_scene_saved_in_temp_directory(validation)

    elif validation_type == "error_message":
        return validate_error_message(validation)

    elif validation_type == "warning_message":
        return validate_warning_message(validation)

    else:
        raise ValueError(
            f"Unknown validation type: {validation_type}"
        )