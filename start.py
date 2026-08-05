from flask import Flask, jsonify, render_template, request

from core.form_parser import build_scenario_from_form
from core.generator import generate_matlab_output
from core.validator import validate_scenario


app = Flask(__name__)
app.json.sort_keys = False
app.jinja_env.policies["json.dumps_kwargs"]["sort_keys"] = False


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/validate")
def validate_api():
    _, validation_result = parse_and_validate_form(request.form)

    return jsonify({
        "validation_result": validation_result,
    })


@app.post("/generate")
def generate():
    scenario, validation_result = parse_and_validate_form(request.form)
    if not validation_result["valid"]:
        return render_template(
            "generated.html",
            generation_result=None,
            validation_result=validation_result,
        ), 400

    generation_result = generate_matlab_output(scenario)

    return render_template(
        "generated.html",
        generation_result=generation_result,
        validation_result=validation_result,
    )


def parse_and_validate_form(form_data):
    scenario = build_scenario_from_form(form_data)
    validation_result = validate_scenario(scenario)

    return scenario, validation_result


if __name__ == "__main__":
    app.run(port=5001)
