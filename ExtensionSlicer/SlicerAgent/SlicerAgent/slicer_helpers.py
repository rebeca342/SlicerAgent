"""
Funciones auxiliares para las tools que se ejecuta dentro de 3D Slicer.

Estas funciones se crearon para hacer más robusta la ejecución de las tools y controlar los errores
que puede generar la LLM como pueden ser:

- Mayusculas y minúsculas
- Espacios en blanco
- Errores al escribir el nombre de los nodos
- Errores en la ruta de los archivos

"""

import os
import difflib
import slicer
import SampleData



# Normalización de nombres


def normalize_name(text):
    """
    Normaliza un nombre de nodo o dataset para comparaciones.
    CT Chest a ctchest

    """

    if text is None:
        return ""

    return (
        str(text)
        .lower()
        .strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )



# Busqueda de nodos en la escena


def find_best_node(node_name="", class_name=None, allowed_classes=None, cutoff=0.7):
    """
    Busca el nodo más adecuado en la escena de Slicer.

    """

    requested = normalize_name(node_name)

    

    if class_name is not None:

        nodes = list(slicer.util.getNodesByClass(class_name))

    else:

        nodes = list(slicer.util.getNodes().values())

        if allowed_classes:

            nodes = [
                node for node in nodes
                if node.GetClassName() in allowed_classes
            ]

    if len(nodes) == 0:
        return None, "No matching nodes are loaded."

    
    # Nombre vacío
    

    if requested == "":

        if len(nodes) == 1:
            return nodes[0], None

        names = "\n".join(node.GetName() for node in nodes)

        return None, (
            "Multiple nodes are available.\n"
            "Please specify one:\n\n"
            f"{names}"
        )

    
    # Coincidencia exacta
    

    for node in nodes:

        if node.GetName() == node_name:
            return node, None

    
    # Normalizar y coincidencia exacta
    

    normalized = {
        normalize_name(node.GetName()): node
        for node in nodes
    }

    if requested in normalized:
        return normalized[requested], None

    
    # Coincidencia parcial
    

    matches = []

    for key, node in normalized.items():

        if requested in key:
            matches.append(node)

    if len(matches) == 1:
        return matches[0], None

    if len(matches) > 1:

        names = "\n".join(node.GetName() for node in matches)

        return None, (
            "Multiple matching nodes found:\n\n"
            f"{names}"
        )

    
    # Fuzzy matching
    

    close = difflib.get_close_matches(
        requested,
        normalized.keys(),
        n=1,
        cutoff=cutoff,
    )

    if close:
        return normalized[close[0]], None

    names = "\n".join(node.GetName() for node in nodes)

    return None, (
        "Node not found.\n\n"
        "Available nodes:\n"
        f"{names}"
    )



# Dataset sample data


def find_demo_dataset(dataset_name="MRHead"):
    """
    Busca un dataset de ejemplo en Slicer.

    """

    requested = normalize_name(dataset_name)

    if requested == "":
        return "MRHead", None

    sampleDataLogic = SampleData.SampleDataLogic()

    datasets = [
        name.replace("download", "")
        for name in dir(sampleDataLogic)
        if name.startswith("download")
    ]

    normalized = {
        normalize_name(name): name
        for name in datasets
    }

    aliases = {

        "head": "MRHead",
        "brain": "MRHead",
        "mrhead": "MRHead",

        "ctchest": "CTChest",
        "chest": "CTChest",
        "thorax": "CTChest",

        "dti": "DTIBrain",
        "dtibrain": "DTIBrain",

        "tumor": "MRBrainTumor1",
        "braintumor": "MRBrainTumor1",
        "mrbraintumor": "MRBrainTumor1",
    }

    if requested in aliases:
        return aliases[requested], None

    if requested in normalized:
        return normalized[requested], None

    partial = []

    for key, value in normalized.items():

        if requested in key:
            partial.append(value)

    if len(partial) == 1:
        return partial[0], None

    if len(partial) > 1:

        names = "\n".join(partial)

        return None, (
            "Multiple matching datasets found:\n\n"
            f"{names}"
        )

    close = difflib.get_close_matches(
        requested,
        normalized.keys(),
        n=1,
        cutoff=0.7,
    )

    if close:
        return normalized[close[0]], None

    names = "\n".join(sorted(datasets))

    return None, (
        "Dataset not found.\n\n"
        "Available datasets:\n"
        f"{names}"
    )



# Archivos


def ensure_output_folder(path):
    """
    Crea la carpeta de salida si no existe.

    """

    folder = os.path.dirname(path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    return path



# Ruta archivos


import time


def ensure_extension(path, extension):
    """
     Se asegura que la ruta del archivo tenga la extensión correcta.

    """

    if not path.lower().endswith(extension.lower()):
        path += extension

    return path


def default_scene_filename():
    """
    Genera un nombre de archivo por defecto para guardar la escena.

    scene_20260708_153522.mrb
    """

    return "scene_" + time.strftime("%Y%m%d_%H%M%S") + ".mrb"



# Comprobación de la escena vacía


def scene_has_data():
    """
    Comprueba si la escena de Slicer tiene datos cargados.

    """

    data_classes = [
        "vtkMRMLScalarVolumeNode",
        "vtkMRMLVectorVolumeNode",
        "vtkMRMLLabelMapVolumeNode",
        "vtkMRMLSegmentationNode",
    ]

    for class_name in data_classes:
        if slicer.mrmlScene.GetNumberOfNodesByClass(class_name) > 0:
            return True

    return False




# Validación de archivos de entrada


def validate_input_file(path, valid_extensions=None, strict_extensions=False, forbid_segmentation=False):
    """
    Valida que un archivo de entrada exista y tenga la extensión correcta.

    """


    if path is None:
        return None, "Empty file path."

    path = str(path).strip()

    if path == "":
        return None, "Empty file path."

    if not os.path.exists(path):
        return None, f"File does not exist:\n{path}"

    if os.path.isdir(path):
        return None, f"Expected a file but received a directory:\n{path}"
    
    lower = path.lower()

    if forbid_segmentation and lower.endswith(".seg.nrrd"):
        return None, (
            "Segmentation files (.seg.nrrd) are not valid volume files."
        )

    if valid_extensions:

        supported = any(
            lower.endswith(ext.lower())
            for ext in valid_extensions
        )

        if not supported:

            if strict_extensions:

                return None, (
                    "Unsupported file extension.\n\n"
                    "Supported extensions:\n"
                    + "\n".join(valid_extensions)
                )

            else:

                print(
                    "WARNING: The file extension is not one of the expected ones."
                )

    return path, None



# Segmentation 3D


def ensure_closed_surface(segmentation_node):
    """
    Asegura que la segmentación tenga una representación de superficie cerrada.

    """

    if segmentation_node is None:
        return "Invalid segmentation."

    success = segmentation_node.CreateClosedSurfaceRepresentation()

    if not success:
        return "Failed to create the closed surface representation."

    return None


