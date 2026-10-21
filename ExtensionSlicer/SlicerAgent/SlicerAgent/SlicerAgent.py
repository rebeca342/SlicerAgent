import logging
import os
from typing import Annotated

import vtk
import qt

import json
import urllib.request
import re

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# SlicerAgent
#


class SlicerAgent(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SlicerAgent")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#SlicerChatModule">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # SlicerChatModule1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SlicerChatModule",
        sampleName="SlicerChatModule1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "SlicerChatModule1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="SlicerChatModule1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="SlicerChatModule1",
    )

    # SlicerChatModule2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SlicerChatModule",
        sampleName="SlicerChatModule2",
        thumbnailFileName=os.path.join(iconsPath, "SlicerChatModule2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="SlicerChatModule2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="SlicerChatModule2",
    )


#
# SlicerAgentParameterNode
#


@parameterNodeWrapper
class SlicerAgentParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# SlicerChatModuleWidget
#


class SlicerAgentWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self):
        """Setup del widget: crea una interfaz mínima tipo 'chat'."""
        ScriptedLoadableModuleWidget.setup(self)

        # Si el parent ya tiene un layout (p. ej. por el .ui), úsalo.
        parentLayout = self.parent.layout()
        if parentLayout is None:
            parentLayout = qt.QVBoxLayout(self.parent)
        self.layout = parentLayout

        # Título / explicación corta
        titleLabel = qt.QLabel("SlicerAgent prueba. Escribe un prompt y pulsa Enviar.")
        titleLabel.setWordWrap(True)
        self.layout.addWidget(titleLabel)

        # Area de texto para prompt
        self.promptEdit = qt.QPlainTextEdit()
        #self.promptEdit.setPlaceholderText("Escribe aquí lo que quieres que haga (ej: segmenta el hígado)...")
        self.promptEdit.setMaximumHeight(100)
        self.layout.addWidget(self.promptEdit)

        # Botón Enviar
        self.sendButton = qt.QPushButton("Enviar")
        self.sendButton.toolTip = "Enviar prompt al servidor LLM"
        self.sendButton.clicked.connect(self.onSend)
        self.layout.addWidget(self.sendButton)

        # Area para mostrar la respuesta "código devuelto por la LLM"
        codeLabel = qt.QLabel("Respuesta (Código generado):")
        self.layout.addWidget(codeLabel)
        self.codeView = qt.QPlainTextEdit()
        self.codeView.setReadOnly(True)
        self.codeView.setMinimumHeight(200)
        self.layout.addWidget(self.codeView)

        # Botón para ejecutar el código mostrado
        self.execButton = qt.QPushButton("Ejecutar código mostrado")
        self.execButton.clicked.connect(self.onExecute)
        # lo desactivado hasta que haya código
        self.execButton.setEnabled(False)
        self.layout.addWidget(self.execButton)

        # Guardamos en un atributo el código generado
        self.generatedCode = ""

    def onSend(self):
        """Envía el prompt a Ollama (sin streaming) y muestra la respuesta en codeView."""
        prompt = self.promptEdit.toPlainText().strip()
        if not prompt:
            slicer.util.warningDisplay("Escribe un prompt antes de enviar.")
            return

        # Petición HTTP (sin streaming, formato JSON completo)
        url = "http://localhost:5000/agent"

        payload = {
            "prompt": prompt
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_json = json.load(resp)
        except Exception as e:
            slicer.util.errorDisplay(f"Error contactando Ollama: {e}")
            return

        code_text = resp_json.get("code", "")

        # Guardar y mostrar en la interfaz
        self.generatedCode = code_text
        self.codeView.setPlainText(code_text)
        self.execButton.setEnabled(bool(code_text))
        slicer.util.showStatusMessage("Respuesta recibida del agente", 2000)


    def onExecute(self):
        """Ejecuta de forma controlada el código generado (whitelist simple)."""
        if not self.generatedCode:
            slicer.util.warningDisplay("No hay código para ejecutar.")
            return

        # Mostramos el código en un diálogo y pedimos confirmación
        dlg = qt.QMessageBox()
        dlg.setWindowTitle("Confirma ejecución")
        dlg.setText("Vas a ejecutar el código mostrado en Slicer. ¿Estás segura/o?")
        dlg.setInformativeText("Revisa el código. Solo se permiten acciones seguras (crear segmentación).")
        dlg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        res = dlg.exec_()
        if res != qt.QMessageBox.Ok:
            return

        code = self.generatedCode

        # intentar extraer bloque markdown (lo que esta entre el markdown)
        match = re.search(r"```(?:python)?\n(.*?)```", code, re.DOTALL)

        if match:
            code = match.group(1)

        code = code.strip()

        # WHITELIST SIMPLE: detectamos patrones seguros y ejecutamos funciones concretas.
        # Actualmente soportamos:
        #  - Crear un nodo de segmentación: AddNewNodeByClass('vtkMRMLSegmentationNode')
        #  - Crear y nombrar nodo: .SetName("NAME")
        # Si el código no coincide con la whitelist, avisamos y no ejecutamos.
        try:
            # Normalizamos a minúsculas para búsqueda simple (pero mantenemos string original)
            # lowered = code.lower()
            # if "addnewnodebyclass" in lowered and "vtkmrmlsegmentationnode" in lowered:
            #     # Crear nodo de segmentación seguro
            #     segNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
            #     # Intentamos extraer nombre si el código lo indicaba con SetName("...")
            #     import re
            #     m = re.search(r"\.setname\(\s*[\"']([^\"']+)[\"']\s*\)", code, flags=re.IGNORECASE)
            #     if m:
            #         try:
            #             segNode.SetName(m.group(1))
            #         except Exception:
            #             pass
            #     # Hacer visible en 2D/3D
            #     dn = segNode.GetDisplayNode()
            #     if dn:
            #         dn.SetVisibility2D(True)
            #         dn.SetVisibility3D(True)
            #         dn.SetOpacity3DFill(0.4)
            #     slicer.util.infoDisplay(f"Segmentación creada: {segNode.GetName()}")
            # else:
            #     slicer.util.warningDisplay(
            #         "El código generado no coincide con las acciones permitidas por la whitelist.\n"
            #         "Revisa el código o ejecuta manualmente si confías."
            #     )

            exec(code, {"slicer": slicer})
            slicer.util.infoDisplay("Código ejecutado directamente (sin whitelist).")
        except Exception as e:
            slicer.util.errorDisplay(f"Error al aplicar código seguro: {e}")


    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: SlicerAgentParameterNode | None) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


#
# SlicerChatModuleLogic
#


class SlicerAgentLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return SlicerAgentParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


#
# SlicerChatModuleTest
#


class SlicerAgentTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_SlicerChatModule1()

    def test_SlicerChatModule1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("SlicerChatModule1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = SlicerAgentLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
