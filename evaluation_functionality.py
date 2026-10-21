"""
evaluation_functionality.py

Evalúa la funcionalidad de los tools.

Flujo de trabajo:
--------
Para cada caso de prueba en el dataset:

1. Generar el código Python usando el tool.
2. Generar el código del validador.
3. Ejecutar ambos dentro de 3D Slicer.
4. Almacenar el resultado.

"""

from pathlib import Path
import json


from functionality_validator import get_validator_code
from Slicer_execution_functionality import run_functionality_test

from tools import (
    set_ct_window_preset,
    load_demo_volume,
    load_volume_from_file,
    load_segmentation_from_file,
    show_segmentation_in_3d,
    save_node_to_file,
    save_scene_as_mrb,
)


# DATASET poner el path correcto del dataset de evaluación de funcionalidad

DATASET_PATH = Path(
    r"C:\Users\Usuario\Documents\MASTER IA\TFM\dataset_functionality.json"
)

OUTPUT_JSON = Path(
    r"C:\Users\Usuario\Documents\MASTER IA\TFM\ResultadosEv_func\functionality_results.json"
)

SUMMARY_PATH = Path(
    r"C:\Users\Usuario\Documents\MASTER IA\TFM\ResultadosEv_func\functionality_summary.txt"
)

LOG_PATH = Path(
    r"C:\Users\Usuario\Documents\MASTER IA\TFM\ResultadosEv_func\functionality_log.txt"
)


# Registro de los tools disponibles


TOOLS = {
    "set_ct_window_preset": set_ct_window_preset,
    "load_demo_volume": load_demo_volume,
    "load_volume_from_file": load_volume_from_file,
    "load_segmentation_from_file": load_segmentation_from_file,
    "show_segmentation_in_3d": show_segmentation_in_3d,
    "save_node_to_file": save_node_to_file,
    "save_scene_as_mrb": save_scene_as_mrb,
}


# Se genera el código Python producido por el tool


def generate_tool_code(example):
    """
    Genera el código Python producido por el tool.

    """

    tool_name = example["tool"]

    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool = TOOLS[tool_name]

    args = example.get("args", {})

    return tool.invoke(args)


# Ejecuta un caso de evaluación de funcionalidad


def evaluate_case(case: dict) ->dict:
    """
    Ejecuta un caso de evaluación de funcionalidad.

    """

    
    # Generar el código del tool
    

    tool_name = case["tool"]

    print("Generating tool code...")
    tool_code = generate_tool_code(case)

    
    # Generar el código del validador
    

    validator_code = get_validator_code(
        case["validation"]
    )

    
    # Cragar escena
    

    scene_path = case["setup"]["scene"]

    
    # Ejecutar Slicer y capturar la salida
    

    print("Running Slicer...")
    execution = run_functionality_test(
        scene_path=scene_path,
        tool_code=tool_code,
        validator_code=validator_code,
    )

    print("Slicer finished.")

    stdout = execution["stdout"]
    stderr = execution["stderr"]

    
    # Interpretar el resultado de la validación
    

    validation_success = (
        "VALIDATION_SUCCESS" in stdout
        and
        "VALIDATION_FAILED" not in stdout
        and
        "VALIDATOR_EXCEPTION" not in stdout
    )

    
    # Construir el resultado del caso de evaluación
    

    result = {
        "id": case["id"],
        "tool": tool_name,
        "expected_result": case["expected_result"],
        "validation_type": case["validation"]["type"],
        "validation_success": validation_success,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": execution["returncode"],
    }

    return result


# Main


def main():

    print("=" * 70)
    print("FUNCTIONALITY EVALUATION")
    print("=" * 70)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("FUNCTIONALITY EVALUATION LOG\n")
        f.write("=" * 70 + "\n\n")

    
    # Cargar dataset de evaluación de funcionalidad
    

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total_cases = len(dataset)

    print(f"Loaded {total_cases} evaluation cases.\n")

    
    # Ejecutar cada caso de evaluación y almacenar los resultados
    

    results = []

    for index, case in enumerate(dataset, start=1):

        print("-" * 70)
        print(f"[{index}/{total_cases}] Case {case['id']} ({case['tool']})")

        try:

            result = evaluate_case(case)

        except Exception as e:

            result = {
                "id": case["id"],
                "tool": case["tool"],
                "expected_result": case["expected_result"],
                "validation_type": case["validation"]["type"],
                "validation_success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }

        results.append(result)

        with open(LOG_PATH, "a", encoding="utf-8") as f:

            f.write("-" * 70 + "\n")
            f.write(f"Case {case['id']} ({case['tool']})\n")
            f.write(f"Validation success: {result['validation_success']}\n")
            f.write(f"Return code: {result['returncode']}\n")

            if result["stderr"]:
                f.write("\nSTDERR\n")
                f.write(result["stderr"])
                f.write("\n")

            if result["stdout"]:
                f.write("\nSTDOUT\n")
                f.write(result["stdout"])
                f.write("\n")

            f.write("\n")

        if result["validation_success"]:
            print("PASSED\n")
        else:
            print("FAILED\n")

    
    # Guardar resultados en JSON
    

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False,
        )

    
    # Estadísticas
    

    passed = sum(
        r["validation_success"]
        for r in results
    )

    failed = len(results) - passed

    success_rate = (
        passed / len(results)
        if results
        else 0
    )
    

    
    # TXT
    

    with open(
        SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("=" * 70 + "\n")
        f.write("FUNCTIONALITY EVALUATION SUMMARY\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total tests: {len(results)}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Success rate: {success_rate:.2%}\n\n")

        f.write("-" * 70 + "\n")
        f.write("PER-TEST RESULTS\n")
        f.write("-" * 70 + "\n\n")

        for r in results:

            status = (
                "PASS"
                if r["validation_success"]
                else "FAIL"
            )

            f.write(
                f"[{status}] "
                f"Case {r['id']} "
                f"({r['tool']})\n"
            )

            if not r["validation_success"]:

                if r["stderr"]:
                    f.write(
                        f"    stderr: {r['stderr']}\n"
                    )

                if r["stdout"]:
                    f.write(
                        f"    stdout: {r['stdout']}\n"
                    )

            f.write("\n")

    

    print("=" * 70)
    print("Evaluation finished")
    print("=" * 70)

    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Success: {success_rate:.2%}")

    print()
    print(f"JSON saved to : {OUTPUT_JSON}")
    print(f"TXT saved to  : {SUMMARY_PATH}")

    return results


if __name__ == "__main__":
    main()
