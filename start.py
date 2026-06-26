from flask import Flask, jsonify, render_template, request

from core.form_parser import build_scenario_from_form
from core.generator import generate_zonotopes
from core.validator import validate_scenario


app = Flask(__name__)
app.json.sort_keys = False
app.jinja_env.policies["json.dumps_kwargs"]["sort_keys"] = False


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/validate")
def validate_api():
    scenario = build_scenario_from_form(request.form)
    validation_result = validate_scenario(scenario)

    return jsonify({
        "validation_result": validation_result,
    })


@app.post("/generate")
def generate():
    scenario = build_scenario_from_form(request.form)
    validation_result = validate_scenario(scenario)
    generation_result = None

    if validation_result["valid"]:
        generation_result = generate_zonotopes(scenario)

    return render_template(
        "generated.html",
        validation_result=validation_result,
        generation_result=generation_result,
    )


if __name__ == "__main__":
    app.run(port=5001)
