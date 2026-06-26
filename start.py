import json

from flask import Flask, render_template, request

from core.form_parser import build_scenario_from_form
from core.generator import generate_zonotopes
from core.validator import validate_scenario


app = Flask(__name__)
app.json.sort_keys = False
app.jinja_env.policies["json.dumps_kwargs"]["sort_keys"] = False


@app.get("/")
def index():
    return render_template(
        "index.html",
        validation_was_requested=False,
        scenario=None,
        validation_result=None,
        generation_result=None,
    )


@app.post("/validate")
def validate():
    scenario = build_scenario_from_form(request.form)
    validation_result = validate_scenario(scenario)

    return render_template(
        "index.html",
        validation_was_requested=True,
        scenario=scenario,
        validation_result=validation_result,
        generation_result=None,
    )


@app.post("/generate")
def generate():
    scenario = json.loads(request.form["scenario_json"])
    validation_result = validate_scenario(scenario)
    generation_result = None

    if validation_result["valid"]:
        generation_result = generate_zonotopes(scenario)

    return render_template(
        "index.html",
        validation_was_requested=True,
        scenario=scenario,
        validation_result=validation_result,
        generation_result=generation_result,
    )


if __name__ == "__main__":
    app.run(port=5001)
