# CPS Uncertainty Specification Tool

Flask prototype for specifying uncertainty in CPS scenarios, validating the input, and generating MATLAB code for zonotope-based uncertainty representations.

## Run locally

Requires Python 3.

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

## What the tool models

The input is a scenario-level specification:

- A scenario has an ID, name, description, models, and optional consistency relations.
- Each model has an ID, name, type, and elements.
- Each element is either uncertain or fixed/reference.
- Uncertain elements support:
  - `interval`: `min`, `max`
  - `probabilistic`: Gaussian `mean`, `std`
  - `binary`: `option_0`, `option_1`
- Fixed/reference elements use `fixed_value`.
- Uncertain elements may include classification metadata based on the uncertainty taxonomy.
- Consistency relations connect existing element IDs and store the declared UPR relation.

The UI also provides five example scenarios from real CPS domains: automotive, water/chemical process, building HVAC, medical device, and wind turbine.

## UI and backend flow

- Flask renders the HTML templates.
- JavaScript dynamically adds/removes models, elements, and consistency relations.
- Form fields use dot-separated names, for example:

```text
scenario.models.0.elements.0.uncertainty.min
```

- On validation, the browser posts the form to `/api/validate`.
- `core/form_parser.py` converts the flat Flask `request.form` data into a nested Python dictionary.
- `core/validator.py` returns structural errors, completeness warnings, and cross-field warnings.
- If there are no structural errors, the UI shows the generate button.
- `/generate` displays the generated MATLAB code and the parsed JSON.

## Validation

Structural errors block generation:

- Scenario requires `scenario_id` and `name`.
- `scenario_id` must match `^[a-z0-9_]+$`.
- At least one model is required.
- Model IDs must be present, unique, and match `^[A-Za-z0-9_]+$`.
- Each model requires a name and at least one element.
- Element IDs must be present, unique, and match `^[A-Za-z0-9_]+$`.
- Each element requires `name`, `symbol`, and `unit`.
- Element symbols must be valid MATLAB identifiers and must not collide.
- Each element must have either `uncertainty` or `fixed_value`.
- Interval uncertainty requires `min < max`.
- Probabilistic uncertainty requires `mean`, `std`, and `std > 0`.
- Binary uncertainty requires two different options.
- Consistency relations require `id`, `from_element_id`, `to_element_id`, `expression`, and `upr_type`.
- Relation IDs must match `^[A-Za-z0-9_]+$`.
- Relation endpoints must reference existing element IDs.

Completeness warnings allow generation:

- Scenario should include at least one consistency relation.
- Consistency relations should include `upr_sigma` and `upr_description`.
- Uncertain elements should include `development_phase` and `reducibility_level`.

Cross-field warnings allow generation:

- `nature = Aleatory` should use `interval` or `probabilistic` uncertainty.
- `reducibility_level = Fully Reducible` should have `nature = Epistemic`.
- `risk_type = High` should have `risk_scale >= 70`.
- `effect_type` should match the selected uncertainty type.
- `discrete probabilistic` warns because the generator has no separate representation for it.
- A consistency relation from an element to itself is reported as a warning.

## Generated output

The generated page shows both:

- MATLAB code
- Parsed JSON

For MATLAB:

- Each interval element becomes a continuous `zonotope(...)`.
- Each probabilistic element is converted to a 95% confidence interval and then to a continuous `zonotope(...)`.
- Each binary element becomes a `logicalZonotope(...)`.
- Each fixed/reference element becomes a MATLAB variable assignment.
- If a model has multiple continuous uncertain elements, a joint continuous zonotope is emitted for that model.
- If a model has multiple binary uncertain elements, a joint logical zonotope is emitted for that model.
- Continuous and binary joint zonotopes are kept separate.
- Consistency relations are printed as comments; they do not currently modify the generated zonotopes.

MATLAB dependencies:

- [CORA](https://github.com/TUMcps/CORA) for continuous zonotopes
- [aalanwar/Logical-Zonotope](https://github.com/aalanwar/Logical-Zonotope) for logical zonotopes
