# CPS Uncertainty Specification Tool

Small Flask prototype for entering uncertainty information for CPS scenarios, validating the input, and generating MATLAB/CORA-style zonotope output.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 start.py
```

Open:

```text
http://127.0.0.1:5001
```

## Current scope

- The UI accepts scenarios with multiple models.
- Each model may contain fixed elements and uncertain elements.
- Each uncertain element generates its own zonotope.
- Models with multiple uncertain elements can also get model-level joint zonotopes.
- Supported uncertainty types:
  - `interval`: `min`, `max`
  - `probabilistic`: `mean`, `std`
  - `binary`: `option_0`, `option_1`
- Consistency relations are validated and printed in the generated MATLAB output as comments. They currently don't affect the generated zonotopes.

## UI and backend flow

- Flask serves the HTML form from `templates/`.
- JavaScript in `static/form.js` dynamically adds/removes models, elements, and consistency relations.
- Form fields use dot-separated names such as `scenario.models.0.elements.0.uncertainty.min`.
- On validation, the browser posts the form to `/api/validate`.
- Flask receives the submitted values through `request.form`.
- `core/form_parser.py` converts the flat form keys into a nested Python dictionary. An example parsed scenario can be found in `example.json`.
- The validator returns errors/warnings as JSON.
- If validation succeeds, the UI shows a **Generate zonotopes** button.
- Generation submits the form to `/generate`, where Python parses it again and displays the MATLAB output and parsed JSON.

## Validation checks

Structural errors block generation:

- Scenario must have `scenario_id` and `name`.
- `scenario_id` must match `^[a-z0-9_]+$`.
- Scenario must contain at least one model.
- Each model must have a unique `id`, a `name`, and at least one element.
- Model IDs must match `^[A-Za-z0-9_]+$`.
- Each element must have unique `id`, `name`, `symbol`, and `unit`.
- Element IDs must match `^[A-Za-z0-9_]+$`.
- Element symbols must be valid MATLAB identifiers and must not collide with another element symbol.
- Each element must have either an `uncertainty` block or a `fixed_value`.
- Interval uncertainty requires `min < max`.
- Probabilistic uncertainty requires `mean`, `std`, and `std > 0`.
- Binary uncertainty requires different `option_0` and `option_1`.
- Consistency relations must have `id`, `from_element_id`, `to_element_id`, `expression`, and `upr_type`.
- Consistency relation IDs must match `^[A-Za-z0-9_]+$`.
- Consistency relations must reference existing element IDs.

Completeness warnings allow generation:

- Scenario should contain at least one consistency relation.
- Consistency relations should include `upr_sigma` and `upr_description`.
- Uncertain elements should include `development_phase` and `reducibility_level`.

Cross-field warnings allow generation:

- `nature = Aleatory` should use `interval` or `probabilistic` uncertainty.
- `reducibility_level = Fully Reducible` should have `nature = Epistemic`.
- `risk_type = High` should have `risk_scale >= 70`.
- `effect_type` should match the selected uncertainty type: `continuous non-deterministic -> interval`, `continuous probabilistic -> probabilistic`, `discrete non-deterministic -> binary`.
- `effect_type = discrete probabilistic` warns because the current generator has no separate discrete-probabilistic representation.

## Generated output

The generated page displays MATLAB text and the parsed JSON. Each uncertain element gets its own zonotope. If a model has multiple continuous uncertain elements, the generator also emits a model-level joint continuous `zonotope(...)`. If a model has multiple binary uncertain elements, it emits a separate model-level joint `logicalZonotope(...)`. Continuous and binary joint zonotopes are kept separate.

Dependencies for running the MATLAB output:

- [CORA](https://github.com/TUMcps/CORA) for continuous zonotopes
- [aalanwar/Logical-Zonotope](https://github.com/aalanwar/Logical-Zonotope) for logical zonotopes
