from langchain_core.tools import tool
import json
from typing import Optional


# GENERATE CT WINDOW/LEVEL

@tool(return_direct=True)
def set_ct_window_preset(
    volume_name: str,
    preset: str,
) -> str:
    """
    Use this tool to apply standard CT window/level presets
    to a loaded scalar volume.

    Supported presets:
    - bone
    - lung
    - soft

    Use when user says:
    - change contrast
    - apply CT window
    - bone window
    - lung preset

    Do NOT use for:
    - loading volumes
    - segmentation display
    """

    
    # Valida preset
    

    if preset is None:
        preset = ""

    preset = preset.strip().lower()

    preset_synonym = {
        # Bone
        "bone": "bone",
        "bones": "bone",
        "osseous": "bone",
        "bony": "bone",

        # Lung
        "lung": "lung",
        "lungs": "lung",
        "pulmonary": "lung",

        # Soft tissue
        "soft": "soft",
        "soft tissue": "soft",
        "soft_tissue": "soft",
        "soft-tissue": "soft",
        "softtissue": "soft",
    }

    preset = preset_synonym.get(preset)

    if preset is None:
        return """
print("ERROR: Invalid CT preset.")
print("Supported presets:")
print(" - bone")
print(" - lung")
print(" - soft")
"""

    presets = {
        "bone": (2000, 300),
        "lung": (1500, -600),
        "soft": (400, 40),
    }

    window, level = presets[preset]

    volume_name = (volume_name or "").strip()

    codigo = f'''
import slicer
from slicer_helpers import find_best_node

try:

    volumeNode, error = find_best_node(
        "{volume_name}",
        "vtkMRMLScalarVolumeNode"
    )

    if error:
        raise Exception(error)

    displayNode = volumeNode.GetDisplayNode()

    if displayNode is None:
        raise Exception("Display node not found.")

    displayNode.SetAutoWindowLevel(False)
    displayNode.SetWindow({window})
    displayNode.SetLevel({level})

    print("SUCCESS: CT window preset applied.")
    print("Volume:", volumeNode.GetName())
    print("Preset:", "{preset}")
    print("Window:", {window})
    print("Level:", {level})

except Exception as e:
    print("ERROR:", str(e))
'''

    return codigo


# LOAD A VOLUME FROM DEMO

@tool(return_direct=True)
def load_demo_volume(
    dataset_name: str = "MRHead"
) -> str:
    """
    Use this tool to load sample datasets included with 3D Slicer.

    Examples:
    - MRHead
    - CTChest
    - DTIBrain
    - MRBrainTumor1

    Use when user says:
    - load sample data
    - load demo volume
    - load MRHead

    Do NOT use for local files.
    """

    if dataset_name is None:
        dataset_name = "MRHead"

    dataset_name = dataset_name.strip()

    codigo = f'''
import SampleData
from slicer_helpers import find_demo_dataset

try:

    datasetName, error = find_demo_dataset("{dataset_name}")

    if error:
        raise Exception(error)

    sampleDataLogic = SampleData.SampleDataLogic()

    downloadFunction = getattr(
        sampleDataLogic,
        "download" + datasetName
    )

    volumeNode = downloadFunction()

    if volumeNode is None:
        raise Exception("Dataset download failed.")

    print("SUCCESS: Dataset loaded")
    print("Dataset:", datasetName)
    print("Node:", volumeNode.GetName())

except Exception as e:
    print("ERROR:", str(e))
'''

    return codigo


# SAVE NODE TO FILE

@tool(return_direct=True)
def save_node_to_file(
    node_name: str,
    file_path: str
) -> str:
    """
    Use this tool ONLY when the user wants to save/export
    an existing node to a file.

    The node must already exist in the current Slicer scene.

    Supported node types:
    - transforms (.tfm, .h5)
    - models (.stl, .obj, .vtk)
    - volumes (.nrrd, .nii.gz)
    - segmentations (.seg.nrrd)

    Examples:
    - save the segmentation as seg.nrrd
    - export the model to STL
    - save the transform

    Do NOT use for saving the entire scene.
    """

    codigo = f'''
import os
import slicer

from slicer_helpers import (
    find_best_node,
    ensure_output_folder,
)

try:

    node, error = find_best_node(
        "{node_name}",
        allowed_classes=[
            "vtkMRMLScalarVolumeNode",
            "vtkMRMLSegmentationNode",
            "vtkMRMLModelNode",
            "vtkMRMLTransformNode",
        ]
    )

    if error:
        raise Exception(error)

    outputPath = r"{file_path}".strip()

    if outputPath == "":
        raise Exception("Empty output path.")

    ensure_output_folder(outputPath)

    storageNode = node.CreateDefaultStorageNode()

    if storageNode is None:
        raise Exception(
            "This node type cannot be saved directly."
        )

    validExtensions = [
        ".nrrd",
        ".nii",
        ".nii.gz",
        ".stl",
        ".obj",
        ".vtk",
        ".tfm",
        ".h5",
        ".seg.nrrd",
    ]

    if not any(outputPath.endswith(ext) for ext in validExtensions):
        print("WARNING: Possible unsupported file extension.")

    storageNode.SetFileName(outputPath)

    success = storageNode.WriteData(node)

    if success:
        print("SUCCESS: Saved to", outputPath)
    else:
        raise Exception("WriteData() failed.")

except Exception as e:
    print("ERROR:", str(e))
'''
    return codigo


# SAVE SCENE AS MRB

@tool(return_direct=True)
def save_scene_as_mrb(
    file_path: str = ""
) -> str:
    """
    Use this tool ONLY when the user wants to save the
    ENTIRE current 3D Slicer scene as a .mrb file.

    The node must already exist in the current Slicer scene.

    This includes:
    - volumes
    - models
    - segmentations
    - transforms
    - layouts
    - the complete scene

    Examples:
    - save the scene
    - save project
    - export current session

    Do NOT use for saving individual nodes.
    """

    if file_path is None:
        file_path = ""

    file_path = file_path.strip()

    codigo = f'''
import os
import slicer

from slicer_helpers import (
    ensure_output_folder,
    ensure_extension,
    default_scene_filename,
    scene_has_data,
)

try:

    
    # Validate scene
    

    if not scene_has_data():
        raise Exception("Scene does not contain any user data.")

    
    # Build output path
    

    filePath = r"{file_path}"

    if filePath == "":

        filePath = os.path.join(
            slicer.app.temporaryPath,
            default_scene_filename()
        )

        print("No output path specified.")
        print("Using:", filePath)

    elif os.path.isdir(filePath):

        filePath = os.path.join(
            filePath,
            default_scene_filename()
        )

        print("Output path is a directory.")
        print("Using:", filePath)

    filePath = ensure_extension(
        filePath,
        ".mrb"
    )

    ensure_output_folder(filePath)

    
    # Existing file
    

    if os.path.exists(filePath):
        print("WARNING: Existing file will be overwritten.")

    
    # Save
    

    success = slicer.util.saveScene(filePath)

    if not success:
        raise Exception("saveScene() failed.")

    print("SUCCESS: Scene saved.")
    print("File:", filePath)

except Exception as e:
    print("ERROR:", str(e))
'''

    return codigo


# LOAD SEGMENTATION FROM FILE

@tool(return_direct=True)
def load_segmentation_from_file(
    file_path: str,
    color_table_path: str = ""
) -> str:
    """
    Use this tool ONLY when the user wants to load a segmentation from a file.

    The file must be loaded from disk.

    Supported formats:
    - .seg.nrrd
    - .nii / .nii.gz
    - .nrrd
    - .stl
    - .obj

    If the file is a labelmap NIfTI, an optional color table
    can also be provided.

    Examples:
    - load a segmentation
    - open this STL file as a segmentation
    - load segmentation
    """
    

    if file_path is None:
        file_path = ""

    if color_table_path is None:
        color_table_path = ""

    codigo = f'''
import slicer

from slicer_helpers import validate_input_file

try:

    
    # Validate segmentation file
    

    filePath, error = validate_input_file(
        r"{file_path}",
        [
            ".seg.nrrd",
            ".nrrd",
            ".nii",
            ".nii.gz",
            ".stl",
            ".obj",
        ],
        strict_extensions=True,
        forbid_segmentation=False,
    )

    if error:
        raise Exception(error)

    
    # Optional color table
    

    colorNode = None

    colorPath = r"{color_table_path}".strip()

    if colorPath != "":

        colorPath, error = validate_input_file(colorPath)

        if error:

            print("WARNING:", error)
            print("Ignoring color table.")

        else:

            colorNode = slicer.util.loadColorTable(colorPath)

            if colorNode:
                print("Color table loaded.")

    
    # Load segmentation

    if colorNode:

        node = slicer.util.loadSegmentation(
            filePath,
            {{
                "colorNodeID": colorNode.GetID()
            }}
        )

    else:

        node = slicer.util.loadSegmentation(filePath)

    if node is None:
        raise Exception(
            "Failed to load segmentation."
        )

    print("SUCCESS: Segmentation loaded.")
    print("Node:", node.GetName())

except Exception as e:
    print("ERROR:", str(e))
'''

    return codigo


# SHOW SEGMENTATION IN 3D

@tool(return_direct=True)
def show_segmentation_in_3d(
    segmentation_name: str
) -> str:
    """
    Use this tool ONLY when the user wants to display
    a segmentation in the 3D view.

    Examples:
    - show the segmentation in 3D
    - show the tumor in 3D
    - render segmentation

    Requires the name of an existing segmentation node.
    """

    codigo = f'''
import slicer

from slicer_helpers import (
    find_best_node,
    ensure_closed_surface,
)

try:

    segmentationNode, error = find_best_node(
        "{segmentation_name}",
        class_name="vtkMRMLSegmentationNode"
    )

    if error:
        raise Exception(error)

    error = ensure_closed_surface(segmentationNode)

    if error:
        raise Exception(error)

    displayNode = segmentationNode.GetDisplayNode()

    if displayNode is None:
        raise Exception("Display node not available.")

    displayNode.SetVisibility3D(True)

    print("SUCCESS: Segmentation shown in 3D.")
    print("Segmentation:", segmentationNode.GetName())

except Exception as e:
    print("ERROR:", str(e))
'''

    return codigo


# LOAD VOLUME FROM FILE

@tool(return_direct=True)
def load_volume_from_file(
    file_path: str,
    node_name: str = "",
    show: bool = True,
    labelmap: bool = False
) -> str:
    """
    Use this tool ONLY when the user wants to load a medical image volume.

    The file must be loaded from disk.

    Supported formats:
    - .nrrd
    - .nii
    - .nii.gz
    - .mha
    - converted DICOM volumes

    Examples:
    - load the CT scan
    - open this NIfTI file
    - load MRI volume

    Do NOT use for segmentations.
    """
    codigo = f'''
import slicer

from slicer_helpers import validate_input_file

try:

    filePath, error = validate_input_file(
        r"{file_path}",
        valid_extensions=[
            ".nrrd",
            ".nii",
            ".nii.gz",
            ".mha",
        ], forbid_segmentation=True
    )

    if error:
        raise Exception(error)

    properties = {{
        "show": {show},
        "labelmap": {labelmap},
    }}

    nodeName = "{node_name}".strip()

    if nodeName:
        properties["name"] = nodeName

    volumeNode = slicer.util.loadVolume(
        filePath,
        properties,
    )

    if volumeNode is None:
        raise Exception(
            "Failed to load the volume."
        )

    print("SUCCESS: Volume loaded.")
    print("Node:", volumeNode.GetName())

except Exception as e:
    print("ERROR:", str(e))
'''
    return codigo



@tool(return_direct=True)
def request_clarification() -> str:
    """
    Use this tool ONLY when the user's intention is ambiguous and
    you cannot determine which 3D Slicer operation they want.

    This is the default fallback tool.

    Use this tool if:
    - the user does not clearly state what they want to do
    - multiple tools could reasonably match the request
    - the request is too vague to identify a single action

    Examples:
    - "Can you help me with this?"
    - "Do something with this scan."
    - "Can you fix it?"
    - "Process this image."
    - "I don't know what to do next."

    Do NOT use this tool if:
    - the user's intention is clear but some parameters are missing
      (in that case, use the correct tool and leave missing parameters empty)
    - the user provides an invalid dataset, node name, or file path
      (the corresponding tool will handle validation)
    - you can clearly identify the requested operation.

    This tool should never modify the Slicer scene.
    It should only ask the user for clarification.
    """

    codigo = '''
print("I couldn't determine exactly what you want to do.")
print()
print("Please describe the operation more specifically.")
print()
print("For example:")
print("- Load a volume")
print("- Load a segmentation")
print("- Show a segmentation in 3D")
print("- Apply a CT window preset")
print("- Save a node")
print("- Save the current scene")
'''

    return codigo



tools = [
    set_ct_window_preset,
    load_demo_volume,
    save_node_to_file,
    save_scene_as_mrb,
    load_segmentation_from_file,
    show_segmentation_in_3d,
    load_volume_from_file,
    request_clarification,
]



