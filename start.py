from flask import Flask, render_template, request

from core.form_parser import build_scenario_from_form


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    submitted = request.method == "POST"
    scenario = build_scenario_from_form(request.form) if submitted else None
    # Next step: pass scenario to validator and MATLAB generator.

    return render_template(
        "index.html",
        submitted=submitted,
        scenario=scenario,
    )


if __name__ == "__main__":
    app.run(port=5001)
