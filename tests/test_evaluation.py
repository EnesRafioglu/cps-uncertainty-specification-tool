import copy
import html
import json
import re
import unittest
from pathlib import Path

from werkzeug.datastructures import ImmutableMultiDict

from core.form_parser import build_scenario_from_form
from core.generator import generate_matlab_output
from core.validator import validate_scenario
from start import app


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset_converted"
SYNTHETIC_FIXTURE = ROOT / "tests" / "fixtures" / "handcrafted_mixed_multivariate.json"
RESULTS_FILE = ROOT / "tests" / "evaluation_results.json"

GENERIC_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
SCENARIO_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
MATLAB_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
MATLAB_KEYWORDS = {
    "break", "case", "catch", "classdef", "continue", "else", "elseif",
    "end", "for", "function", "global", "if", "otherwise", "parfor",
    "persistent", "return", "spmd", "switch", "try", "while",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_corpus():
    return [load_json(path) for path in sorted(DATASET_DIR.glob("*/*.json"))]


def flatten_for_form(value, prefix="scenario"):
    pairs = []

    def visit(current, path):
        if isinstance(current, dict):
            for key, child in current.items():
                visit(child, f"{path}.{key}")
        elif isinstance(current, list):
            for index, child in enumerate(current):
                visit(child, f"{path}.{index}")
        else:
            pairs.append((path, str(current)))

    visit(value, prefix)
    return ImmutableMultiDict(pairs)


def omit_empty_form_values(value):
    if isinstance(value, dict):
        return {
            key: omit_empty_form_values(child)
            for key, child in value.items()
            if child != ""
        }
    if isinstance(value, list):
        return [omit_empty_form_values(child) for child in value]
    return value


def extract_preformatted_json(response_text):
    match = re.search(
        r'<pre id="json-output" class="code-block">(.*?)</pre>',
        response_text,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError("Generated page does not contain JSON output")
    return json.loads(html.unescape(match.group(1)))


def expected_structural_validity(scenario):
    if not all(field in scenario for field in ("scenario_id", "name")):
        return False
    if not SCENARIO_ID_PATTERN.fullmatch(str(scenario["scenario_id"])):
        return False
    if not scenario.get("models"):
        return False

    model_ids = set()
    element_ids = set()
    symbols = set()

    for model in scenario["models"]:
        if not all(field in model for field in ("id", "name")):
            return False
        if model["id"] in model_ids or not GENERIC_ID_PATTERN.fullmatch(str(model["id"])):
            return False
        model_ids.add(model["id"])
        if not model.get("elements"):
            return False

        for element in model["elements"]:
            if not all(field in element for field in ("id", "name", "symbol", "unit")):
                return False
            if element["id"] in element_ids or not GENERIC_ID_PATTERN.fullmatch(str(element["id"])):
                return False
            element_ids.add(element["id"])
            symbol = str(element["symbol"])
            if symbol in symbols or not MATLAB_ID_PATTERN.fullmatch(symbol) or symbol in MATLAB_KEYWORDS:
                return False
            symbols.add(symbol)

            if "uncertainty" not in element and "fixed_value" not in element:
                return False
            if "uncertainty" not in element:
                continue

            uncertainty = element["uncertainty"]
            uncertainty_type = uncertainty.get("type")
            if uncertainty_type == "interval":
                if "min" not in uncertainty or "max" not in uncertainty:
                    return False
                if uncertainty["min"] >= uncertainty["max"]:
                    return False
            elif uncertainty_type == "probabilistic":
                if "mean" not in uncertainty or "std" not in uncertainty:
                    return False
                if uncertainty["std"] <= 0:
                    return False
            elif uncertainty_type == "binary":
                if "option_0" not in uncertainty or "option_1" not in uncertainty:
                    return False
                if uncertainty["option_0"] == uncertainty["option_1"]:
                    return False
            else:
                return False

    relation_ids = set()
    for relation in scenario.get("consistency_relations", []):
        required = ("id", "from_element_id", "to_element_id", "expression", "upr_type")
        if not all(field in relation for field in required):
            return False
        if relation["id"] in relation_ids or not GENERIC_ID_PATTERN.fullmatch(str(relation["id"])):
            return False
        relation_ids.add(relation["id"])
        if relation["from_element_id"] not in element_ids or relation["to_element_id"] not in element_ids:
            return False

    return True


def expected_element_snippets(element):
    symbol = element["symbol"]
    if "fixed_value" in element:
        return [f"{symbol} = {element['fixed_value']};"]

    uncertainty = element["uncertainty"]
    uncertainty_type = uncertainty["type"]
    if uncertainty_type == "interval":
        return [
            f"{symbol}_min = {uncertainty['min']};",
            f"{symbol}_max = {uncertainty['max']};",
            f"{symbol}_c = ({symbol}_min + {symbol}_max) / 2;",
            f"{symbol}_G = ({symbol}_max - {symbol}_min) / 2;",
            f"{symbol}_Z = zonotope([{symbol}_c, {symbol}_G]);",
        ]
    if uncertainty_type == "probabilistic":
        return [
            f"{symbol}_mean = {uncertainty['mean']};",
            f"{symbol}_std = {uncertainty['std']};",
            f"{symbol}_confidence_factor = 1.96;",
            f"{symbol}_c = {symbol}_mean;",
            f"{symbol}_G = {symbol}_confidence_factor * {symbol}_std;",
            f"{symbol}_Z = zonotope([{symbol}_c, {symbol}_G]);",
        ]
    return [
        f"{symbol}_c_L = 0;",
        f"{symbol}_G_L = {{1}};",
        f"{symbol}_Z = logicalZonotope({symbol}_c_L, {symbol}_G_L);",
    ]


def expected_model_snippets(model, model_index):
    continuous = [
        element["symbol"]
        for element in model["elements"]
        if element.get("uncertainty", {}).get("type") in {"interval", "probabilistic"}
    ]
    binary = [
        element["symbol"]
        for element in model["elements"]
        if element.get("uncertainty", {}).get("type") == "binary"
    ]
    snippets = []

    if len(continuous) > 1:
        base = f"model_{model_index}_continuous"
        snippets.extend([
            f"{base}_c = [{'; '.join(f'{symbol}_c' for symbol in continuous)}];",
            f"{base}_G = diag([{'; '.join(f'{symbol}_G' for symbol in continuous)}]);",
            f"{base}_Z = zonotope([{base}_c, {base}_G]);",
        ])

    if len(binary) > 1:
        base = f"model_{model_index}_binary"
        dimension_count = len(binary)
        snippets.extend([
            f"{base}_c_L = zeros({dimension_count}, 1);",
            f"{base}_G_L = num2cell(logical(eye({dimension_count})), 1);",
            f"{base}_Z = logicalZonotope({base}_c_L, {base}_G_L);",
        ])

    return snippets


def mutate(base, name, tier, message_fragment, operation):
    scenario = copy.deepcopy(base)
    operation(scenario)
    return {
        "name": name,
        "tier": tier,
        "message_fragment": message_fragment,
        "scenario": scenario,
    }


def robustness_mutations(base):
    cases = []

    def add(name, tier, message, operation):
        cases.append(mutate(base, name, tier, message, operation))

    add("missing scenario ID", "structural_errors", "Scenario is missing", lambda s: s.pop("scenario_id"))
    add("malformed scenario ID", "structural_errors", "Scenario ID must match pattern", lambda s: s.update(scenario_id="Bad-ID"))
    add("empty model list", "structural_errors", "does not have any models", lambda s: s.update(models=[]))
    add("missing model ID", "structural_errors", "does not have an ID", lambda s: s["models"][0].pop("id"))
    add("duplicate model ID", "structural_errors", "does not have a unique ID", lambda s: s["models"][1].update(id="M1"))
    add("empty element list", "structural_errors", "does not have any elements", lambda s: s["models"][0].update(elements=[]))
    add("missing element unit", "structural_errors", "required fields: unit", lambda s: s["models"][0]["elements"][0].pop("unit"))
    add("duplicate element ID", "structural_errors", "does not have a unique ID", lambda s: s["models"][0]["elements"][1].update(id="e1"))
    add("invalid MATLAB symbol", "structural_errors", "must be a valid MATLAB identifier", lambda s: s["models"][0]["elements"][0].update(symbol="1-invalid"))
    add("duplicate MATLAB symbol", "structural_errors", "conflicts with another MATLAB identifier", lambda s: s["models"][0]["elements"][1].update(symbol="x_interval"))
    add("element without value", "structural_errors", "neither uncertainty nor a fixed value", lambda s: s["models"][0]["elements"][0].pop("uncertainty"))
    add("missing interval bound", "structural_errors", "missing min or max", lambda s: s["models"][0]["elements"][0]["uncertainty"].pop("max"))
    add("reversed interval", "structural_errors", "min is not smaller than max", lambda s: s["models"][0]["elements"][0]["uncertainty"].update(min=6, max=-2))
    add("missing standard deviation", "structural_errors", "missing mean or std", lambda s: s["models"][0]["elements"][1]["uncertainty"].pop("std"))
    add("non-positive standard deviation", "structural_errors", "std is not greater than 0", lambda s: s["models"][0]["elements"][1]["uncertainty"].update(std=0))
    add("missing binary option", "structural_errors", "options are not specified", lambda s: s["models"][0]["elements"][2]["uncertainty"].pop("option_1"))
    add("equal binary options", "structural_errors", "options are the same", lambda s: s["models"][0]["elements"][2]["uncertainty"].update(option_1="disabled"))
    add("missing relation field", "structural_errors", "missing the following required fields: upr_type", lambda s: s["consistency_relations"][0].pop("upr_type"))

    def duplicate_relation(scenario):
        scenario["consistency_relations"].append(copy.deepcopy(scenario["consistency_relations"][0]))

    add("duplicate relation ID", "structural_errors", "does not have a unique ID", duplicate_relation)
    add("dangling relation reference", "structural_errors", "does not reference valid elements", lambda s: s["consistency_relations"][0].update(to_element_id="missing"))
    add("missing relations", "completeness_warnings", "does not have any consistency relations", lambda s: s.update(consistency_relations=[]))

    def remove_upr_metadata(scenario):
        scenario["consistency_relations"][0].pop("upr_sigma")
        scenario["consistency_relations"][0].pop("upr_description")

    add("missing UPR metadata", "completeness_warnings", "missing recommended UPR fields", remove_upr_metadata)

    def remove_classification_metadata(scenario):
        classification = scenario["models"][0]["elements"][0]["classification"]
        classification.pop("development_phase")
        classification.pop("reducibility_level")

    add("missing classification metadata", "completeness_warnings", "missing recommended classification fields", remove_classification_metadata)
    add("same relation endpoint", "cross_field_warnings", "same element as both source and target", lambda s: s["consistency_relations"][0].update(to_element_id="e1"))
    add("aleatory binary value", "cross_field_warnings", "nature Aleatory", lambda s: s["models"][0]["elements"][2]["classification"].update(nature="Aleatory"))

    def fully_reducible_aleatory(scenario):
        classification = scenario["models"][0]["elements"][0]["classification"]
        classification.update(reducibility_level="Fully Reducible", nature="Aleatory")

    add("fully reducible aleatory value", "cross_field_warnings", "Fully Reducible but nature is not Epistemic", fully_reducible_aleatory)

    def high_risk_low_scale(scenario):
        scenario["models"][0]["elements"][0]["classification"].update(risk_type="High", risk_scale=20)

    add("high risk with low scale", "cross_field_warnings", "risk scale is below 70", high_risk_low_scale)
    add("effect-type mismatch", "cross_field_warnings", "expected probabilistic", lambda s: s["models"][0]["elements"][0]["classification"].update(effect_type="continuous probabilistic"))
    add("unsupported discrete probabilistic effect", "cross_field_warnings", "does not support a separate discrete probabilistic", lambda s: s["models"][0]["elements"][2]["classification"].update(effect_type="discrete probabilistic"))
    return cases


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_corpus()
        cls.synthetic = load_json(SYNTHETIC_FIXTURE)
        cls.report = {
            "corpus": {
                "scenarios": len(cls.corpus),
                "synthetic_scenarios": 1,
            }
        }
        app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        RESULTS_FILE.write_text(json.dumps(cls.report, indent=2) + "\n", encoding="utf-8")

    def test_01_form_reconstruction_and_flask_output(self):
        parser_mismatches = []
        route_mismatches = []
        validation_mismatches = []
        expected_accepted = 0
        expected_rejected = 0

        with app.test_client() as client:
            for original in self.corpus:
                scenario_id = original["scenario_id"]
                form_data = flatten_for_form(original)
                expected = omit_empty_form_values(original)
                actual = build_scenario_from_form(form_data)
                if actual != expected:
                    parser_mismatches.append(scenario_id)

                expected_valid = expected_structural_validity(expected)
                expected_accepted += int(expected_valid)
                expected_rejected += int(not expected_valid)
                validation = validate_scenario(actual)
                if validation["valid"] != expected_valid:
                    validation_mismatches.append(scenario_id)

                response = client.post("/generate", data=form_data)
                expected_status = 200 if expected_valid else 400
                if response.status_code != expected_status:
                    route_mismatches.append(f"{scenario_id}: status {response.status_code}")
                    continue

                rendered_json = extract_preformatted_json(response.get_data(as_text=True))
                if rendered_json != expected:
                    route_mismatches.append(f"{scenario_id}: JSON mismatch")

        self.__class__.report["form_reconstruction"] = {
            "direct_matches": len(self.corpus) - len(parser_mismatches),
            "direct_total": len(self.corpus),
            "route_json_matches": len(self.corpus) - len(route_mismatches),
            "route_total": len(self.corpus),
            "structurally_accepted": expected_accepted,
            "structurally_rejected": expected_rejected,
            "validation_outcome_matches": len(self.corpus) - len(validation_mismatches),
        }

        self.assertEqual([], parser_mismatches)
        self.assertEqual([], route_mismatches)
        self.assertEqual([], validation_mismatches)

    def test_02_corpus_matlab_generation(self):
        uncertain_element_failures = []
        fixed_element_failures = []
        model_failures = []
        relation_failures = []
        uncertain_total = 0
        fixed_total = 0
        joint_continuous_total = 0
        joint_binary_total = 0

        for scenario in self.corpus:
            output = generate_matlab_output(scenario)
            for model_index, model in enumerate(scenario["models"], start=1):
                continuous_count = 0
                binary_count = 0
                for element in model["elements"]:
                    if "uncertainty" in element:
                        uncertain_total += 1
                        uncertainty_type = element["uncertainty"]["type"]
                        continuous_count += int(uncertainty_type in {"interval", "probabilistic"})
                        binary_count += int(uncertainty_type == "binary")
                    else:
                        fixed_total += 1

                    missing = [snippet for snippet in expected_element_snippets(element) if snippet not in output]
                    if missing:
                        failure = {
                            "scenario": scenario["scenario_id"],
                            "element": element["id"],
                            "missing": missing,
                        }
                        if "uncertainty" in element:
                            uncertain_element_failures.append(failure)
                        else:
                            fixed_element_failures.append(failure)

                joint_continuous_total += int(continuous_count > 1)
                joint_binary_total += int(binary_count > 1)
                missing = [
                    snippet
                    for snippet in expected_model_snippets(model, model_index)
                    if snippet not in output
                ]
                if missing:
                    model_failures.append({
                        "scenario": scenario["scenario_id"],
                        "model": model["id"],
                        "missing": missing,
                    })

            for relation in scenario.get("consistency_relations", []):
                expected = f"% {relation['id']} [{relation['upr_type']}]: {relation['expression']}"
                if expected not in output:
                    relation_failures.append({
                        "scenario": scenario["scenario_id"],
                        "relation": relation["id"],
                    })

        relation_total = sum(len(scenario.get("consistency_relations", [])) for scenario in self.corpus)
        self.__class__.report["corpus_matlab_generation"] = {
            "uncertain_element_matches": uncertain_total - len(uncertain_element_failures),
            "uncertain_element_total": uncertain_total,
            "fixed_element_matches": fixed_total - len(fixed_element_failures),
            "fixed_element_total": fixed_total,
            "joint_continuous_matches": joint_continuous_total - len(model_failures),
            "joint_continuous_total": joint_continuous_total,
            "joint_binary_matches": joint_binary_total,
            "joint_binary_total": joint_binary_total,
            "relation_comment_matches": relation_total - len(relation_failures),
            "relation_comment_total": relation_total,
        }

        self.assertEqual([], uncertain_element_failures)
        self.assertEqual([], fixed_element_failures)
        self.assertEqual([], model_failures)
        self.assertEqual([], relation_failures)

    def test_03_handcrafted_multivariate_generation(self):
        form_data = flatten_for_form(self.synthetic)
        reconstructed = build_scenario_from_form(form_data)
        validation = validate_scenario(reconstructed)
        output = generate_matlab_output(reconstructed)
        expected_snippets = []
        for model_index, model in enumerate(self.synthetic["models"], start=1):
            for element in model["elements"]:
                expected_snippets.extend(expected_element_snippets(element))
            expected_snippets.extend(expected_model_snippets(model, model_index))

        missing = [snippet for snippet in expected_snippets if snippet not in output]
        self.__class__.report["synthetic_multivariate"] = {
            "form_reconstruction": reconstructed == self.synthetic,
            "structurally_valid": validation["valid"],
            "expected_source_fragments": len(expected_snippets),
            "matching_source_fragments": len(expected_snippets) - len(missing),
            "joint_continuous_generated": "model_1_continuous_G = diag([x_interval_G; y_gaussian_G]);" in output,
            "joint_binary_generated": "model_1_binary_G_L = num2cell(logical(eye(2)), 1);" in output,
        }

        self.assertEqual(self.synthetic, reconstructed)
        self.assertTrue(validation["valid"], validation["structural_errors"])
        self.assertEqual([], missing)

    def test_04_robustness_mutations(self):
        cases = robustness_mutations(self.synthetic)
        detection_failures = []
        tier_failures = []
        gating_failures = []
        crashes = []

        with app.test_client() as client:
            for case in cases:
                name = case["name"]
                tier = case["tier"]
                try:
                    result = validate_scenario(case["scenario"])
                    matching_tiers = [
                        candidate
                        for candidate in ("structural_errors", "completeness_warnings", "cross_field_warnings")
                        if any(case["message_fragment"] in message for message in result[candidate])
                    ]
                    if not matching_tiers:
                        detection_failures.append(name)
                    elif tier not in matching_tiers:
                        tier_failures.append({"name": name, "actual": matching_tiers, "expected": tier})

                    response = client.post("/generate", data=flatten_for_form(case["scenario"]))
                    expected_status = 400 if tier == "structural_errors" else 200
                    has_matlab = 'id="matlab-output"' in response.get_data(as_text=True)
                    expected_matlab = tier != "structural_errors"
                    if response.status_code != expected_status or has_matlab != expected_matlab:
                        gating_failures.append({
                            "name": name,
                            "status": response.status_code,
                            "matlab": has_matlab,
                        })
                except Exception as error:  # pragma: no cover - recorded as an evaluation failure
                    crashes.append({"name": name, "error": repr(error)})

        self.__class__.report["robustness"] = {
            "mutations": len(cases),
            "detected": len(cases) - len(detection_failures),
            "correct_tier": len(cases) - len(tier_failures) - len(detection_failures),
            "correct_gating": len(cases) - len(gating_failures) - len(crashes),
            "crash_free": len(cases) - len(crashes),
            "detection_failures": detection_failures,
            "tier_failures": tier_failures,
            "gating_failures": gating_failures,
            "crashes": crashes,
        }

        self.assertEqual([], detection_failures)
        self.assertEqual([], tier_failures)
        self.assertEqual([], gating_failures)
        self.assertEqual([], crashes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
