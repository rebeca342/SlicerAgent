from flask import Flask, request, jsonify
from agenteOllama import agent_executor
import traceback

app = Flask(__name__)

@app.route("/agent", methods=["POST"])
def run_agent():

    data = request.json
    prompt = data.get("prompt", "")

    try:
        result = agent_executor.invoke({"input": prompt})
        code = result.get("output", "")

        return jsonify({
            "code": code
        })

    except Exception as e:
        traceback.print_exc()  
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(port=5000)