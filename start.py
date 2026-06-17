from flask import Flask, render_template, request

from core.form_parser import build_scenario_from_form


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    submitted = request.method == "POST"
    # Next step: pass scenario to validator and MATLAB generator.

    return render_template(
        "index.html",
        submitted=submitted,
        scenario=None,
    )


if __name__ == "__main__":
    app.run(port=5001)
