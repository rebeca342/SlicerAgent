import json
import re
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from collections import defaultdict

from agenteOllama import agent_executor
from Slicer_execution import run_code_in_slicer



# 1. CARGAR DATASET


DATASET_PATH = "dataset_evaluation.json"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = json.load(f)



# 2. FUNCIONs AUXILIARES

DEFAULT_TOOL_ARGS = {
    "load_volume_from_file": {
        "node_name": "",
        "show": True,
        "labelmap": False,
    },

    "load_demo_volume": {
        "dataset_name": "MRHead",
    },

    "load_segmentation_from_file": {
        "color_table_path": "",
    },

    "save_scene_as_mrb": {
        "file_path": "",
    },
}

def compare_arguments(expected_args, predicted_args, tool_name):
    """
    Comprueba que todos los argumentos esperados están presentes
    y tienen el valor correcto.
    """

    predicted_args = predicted_args.copy()

    defaults = DEFAULT_TOOL_ARGS.get(tool_name, {})

    for key, value in defaults.items():
        predicted_args.setdefault(key, value)

    for key, expected_value in expected_args.items():

        predicted_value = predicted_args.get(key)

        if isinstance(expected_value, str) and isinstance(predicted_value, str):

            expected_value = os.path.normpath(expected_value)

            predicted_value = os.path.normpath(predicted_value)

        if predicted_value != expected_value:
            return False

    return True


# 3. EVALUACIÓN PRINCIPAL


results = []

for item in dataset:
    prompt = item["prompt"]

    print("\n==============================")
    print(f"ID {item['id']} | {prompt}")

    try:
        response = agent_executor.invoke({"input": prompt})

        generated_code = response.get("output", "") # codigo generado por el agente

        print("Launching Slicer")

        print("GENERATED CODE")
        print(repr(generated_code))

        code_result = run_code_in_slicer(generated_code)

        print("Returned from Slicer")

        code_execution_success = code_result["success"]
        code_returncode = code_result["returncode"]
        code_stdout = code_result["stdout"]
        code_stderr = code_result["stderr"]

        executionagent_ok = True # El agente ha respondido a la peticion
        
        steps = response.get("intermediate_steps", [])

        print("\nINTERMEDIATE STEPS")
        print(steps)

        used_tools = [step[0].tool for step in steps]

        num_tools_used = len(used_tools)

        expected_tool = item["expected_tool"]
        expected_args = item["expected_args"]

        if steps:
            action = steps[-1][0]

            predicted_tool = action.tool

            # Obtener los argumentos utilizados por la tool
            predicted_args = getattr(action, "tool_input", {})

            print("\nEXPECTED ARGS")
            print(expected_args)

            print("\nPREDICTED ARGS")
            print(predicted_args)

            print("\nACTION")
            print(action)

            print("Tool:")
            print(action.tool)

            print("Tool input:")
            print(action.tool_input)

            print("Tool input type:")
            print(type(action.tool_input))

        else:
            predicted_tool = None
            predicted_args = {}


        tool_correct = (predicted_tool == expected_tool)

        if tool_correct:
            print("\nCOMPARING")

            print(expected_args)

            print(predicted_args)

            args_match = compare_arguments(expected_args, predicted_args, predicted_tool)
        else:
            args_match = None

        results.append({
            "id": item["id"],
            "prompt": prompt,
            "expected_tool": expected_tool,
            "predicted_tool": predicted_tool,
            "tool_correct": tool_correct,
            "category": item["category"],
            "executionagent_ok": executionagent_ok,
            "num_tools_used": num_tools_used,
            "used_tools": used_tools,
            "expected_args": expected_args,
            "predicted_args": predicted_args,
            "args_match": args_match,
            "generated_code": generated_code,
            "code_execution_success": code_execution_success,
            "code_returncode": code_returncode,
            "code_stdout": code_stdout,
            "code_stderr": code_stderr,
            "raw_output": str(response)
        })

        print(f"Expected: {expected_tool}")
        print(f"Predicted: {predicted_tool}")
        print(f"Used tools: {used_tools}")
        print(f"Number of tools: {num_tools_used}")
        print(f"Correct: {tool_correct}")
        print(f"Expected args: {expected_args}")
        print(f"Predicted args: {predicted_args}")
        
        if args_match is None:
            print("Arguments: NOT EVALUATED (tool mismatch)")
        else:
            print(f"Arguments correct: {args_match}")

    except Exception as e:
        executionagent_ok = False

        results.append({
            "id": item["id"],
            "prompt": prompt,
            "expected_tool": item["expected_tool"],
            "predicted_tool": None,
            "tool_correct": False,
            "category": item["category"],
            "executionagent_ok": executionagent_ok,
            "num_tools_used": 0,
            "used_tools": [],
            "expected_args": item["expected_args"],
            "predicted_args": {},
            "args_match": False,
            "generated_code": "",
            "code_execution_success": False,
            "code_returncode": None,
            "code_stdout": "",
            "code_stderr": str(e),
            "error": str(e)
        })

        print("ERROR:", str(e))



# 4. MÉTRICAS

df = pd.DataFrame(results)

total = len(df)

tool_accuracy = df["tool_correct"].mean()

evaluated_args = df[df["args_match"].notna()]
args_accuracy = evaluated_args["args_match"].mean()

code_accuracy = df["code_execution_success"].mean()

tool_correct = df["tool_correct"].sum()

args_correct = evaluated_args["args_match"].sum()
args_total = len(evaluated_args)

code_correct = df["code_execution_success"].sum()



print("GLOBAL METRICS")


print(f"Tool selection accuracy: {tool_accuracy:.4f}")
print(f"Arguments accuracy:      {args_accuracy:.4f}")
print(f"Code execution accuracy:{code_accuracy:.4f}")



# ACCURACY POR CATEGORÍA

tool_category = (
    df.groupby("category")["tool_correct"]
    .mean()
)

args_category = (
    df[df["args_match"].notna()]
    .groupby("category")["args_match"]
    .mean()
)

code_category = (
    df.groupby("category")["code_execution_success"]
    .mean()
)


print("\nTOOL ACCURACY BY CATEGORY")

for cat, value in tool_category.items():
    print(cat, round(value,4))

print("\nARGUMENT ACCURACY BY CATEGORY")

for cat, value in args_category.items():
    print(cat, round(value,4))

print("\nCODE EXECUTION ACCURACY BY CATEGORY")

for cat, value in code_category.items():
    print(cat, round(value,4))



# GUARDAR MÉTRICAS EN TXT

with open("metric_mistral.txt","w",encoding="utf8") as f:

    f.write("GLOBAL METRICS\n")
    

    f.write(
        f"Tool selection accuracy : {tool_accuracy:.4f} "
        f"({tool_correct}/{total})\n"
    )

    f.write(
        f"Arguments accuracy      : {args_accuracy:.4f} "
        f"({args_correct}/{args_total})\n"
    )

    f.write(
        f"Code execution accuracy : {code_accuracy:.4f} "
        f"({code_correct}/{total})\n\n"
    )


    f.write("TOOL ACCURACY BY CATEGORY\n")

    for cat,value in tool_category.items():
        f.write(f"{cat}: {value:.4f}\n")


    f.write("\nARGUMENT ACCURACY BY CATEGORY\n")

    for cat,value in args_category.items():
        f.write(f"{cat}: {value:.4f}\n")


    f.write("\nCODE EXECUTION ACCURACY BY CATEGORY\n")

    for cat,value in code_category.items():
        f.write(f"{cat}: {value:.4f}\n")

    f.write("\n\nFAILED TOOL SELECTION\n")
    f.write("=====================\n")

    for _, row in df[df["tool_correct"] == False].iterrows():

        f.write(f"\nID: {row['id']}\n")
        f.write(f"Prompt: {row['prompt']}\n")
        f.write(f"Expected tool: {row['expected_tool']}\n")
        f.write(f"Predicted tool: {row['predicted_tool']}\n")
    
    f.write("\n\nFAILED ARGUMENT MATCHING\n")
    f.write("========================\n")

    for _, row in df[df["args_match"] == False].iterrows():

        f.write(f"\nID: {row['id']}\n")
        f.write(f"Prompt: {row['prompt']}\n")
        f.write(f"Expected args: {row['expected_args']}\n")
        f.write(f"Predicted args: {row['predicted_args']}\n")
    
    f.write("\n\nFAILED CODE EXECUTION\n")
    f.write("=====================\n")

    for _, row in df[df["code_execution_success"] == False].iterrows():

        f.write(f"\nID: {row['id']}\n")
        f.write(f"Prompt: {row['prompt']}\n")
        f.write(f"Return code: {row['code_returncode']}\n")
        f.write(f"stderr:\n{row['code_stderr']}\n")


print("\nSaved metrics.txt")



# EXPORTAR RESULTADOS


df.to_csv("evaluation_results_mistral.csv",index=False)

with open("evaluation_results_mistral.json","w",encoding="utf8") as f:
    json.dump(results,f,indent=2,ensure_ascii=False)

print("Saved evaluation_results_mistral.csv")
print("Saved evaluation_results_mistral.json")



# MATRIZ CONFUSIÓN TOOLS


df_cm = df.copy()
df_cm["predicted_tool"] = df_cm["predicted_tool"].fillna("NO_TOOL")

labels = sorted(
    set(df_cm["expected_tool"]) |
    set(df_cm["predicted_tool"])
)

cm = confusion_matrix(
    df_cm["expected_tool"],
    df_cm["predicted_tool"],
    labels=labels
)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=labels
)

fig, ax = plt.subplots(figsize=(12,10))
disp.plot(ax=ax,xticks_rotation=45,cmap="Blues",values_format="d")
plt.xticks(rotation=45,ha="right",fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig("confusion_tools_mistral.png",dpi=300)
plt.close()



# GRÁFICO ARGUMENT MATCHING


correct_args = evaluated_args["args_match"].sum()
incorrect_args = len(evaluated_args) - correct_args

plt.figure(figsize=(5,5))

plt.bar(
    ["Correct", "Incorrect"],
    [correct_args, incorrect_args]
)

plt.title("Argument Matching")
plt.ylabel("Number of samples")

for i, value in enumerate([correct_args, incorrect_args]):
    plt.text(i, value, str(value), ha="center", va="bottom")

plt.tight_layout()
plt.savefig("arguments_matching_mistral.png", dpi=300)
plt.close()



# GRÁFICO CODE EXECUTION


successful = df["code_execution_success"].sum()
failed = len(df) - successful

plt.figure(figsize=(5,5))

plt.bar(
    ["Success", "Failure"],
    [successful, failed]
)

plt.title("Code Execution")
plt.ylabel("Number of samples")

for i, value in enumerate([successful, failed]):
    plt.text(i, value, str(value), ha="center", va="bottom")

plt.tight_layout()
plt.savefig("code_execution_mistral.png", dpi=300)
plt.close()


print("\nSaved:")
print("confusion_tools_mistral.png")
print("arguments_matching_mistral.png")
print("code_execution_mistral.png")