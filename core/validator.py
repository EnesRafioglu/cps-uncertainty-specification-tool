import re

from core.constants import (
   CONTINUOUS_UNCERTAINTY_TYPES,
   ELEMENT_REQUIRED_FIELDS,
   EFFECT_TYPE_TO_UNCERTAINTY_TYPE,
   GENERIC_ID_REGEX,
   INTERVAL,
   MATLAB_IDENTIFIER_REGEX,
   MATLAB_KEYWORDS,
   MODEL_REQUIRED_FIELDS,
   PROBABILISTIC,
   RECOMMENDED_CLASSIFICATION_FIELDS,
   RECOMMENDED_RELATION_FIELDS,
   RELATION_REQUIRED_FIELDS,
   SCENARIO_ID_REGEX,
   SCENARIO_REQUIRED_FIELDS,
   UNSUPPORTED_EFFECT_TYPES,
)

MATLAB_IDENTIFIER_PATTERN = re.compile(MATLAB_IDENTIFIER_REGEX)
SCENARIO_ID_PATTERN = re.compile(SCENARIO_ID_REGEX)
GENERIC_ID_PATTERN = re.compile(GENERIC_ID_REGEX)


def validate_scenario(scenario: dict) -> dict:
   structural_errors = check_structural_rules(scenario)
   completeness_warnings = check_completeness_rules(scenario)
   cross_field_warnings = check_cross_field_rules(scenario)

   return {
      "valid": len(structural_errors) == 0,
      "structural_errors": structural_errors,
      "completeness_warnings": completeness_warnings,
      "cross_field_warnings": cross_field_warnings,
   }


def check_structural_rules(scenario: dict) -> list:
   errors = []
   seen_model_ids, seen_element_ids, seen_relation_ids = set(), set(), set()
   seen_matlab_symbols = set()

   check_scenario_identity(errors, scenario)

   if not scenario.get("models"):
      errors.append("Scenario does not have any models")

   for model_index, model in enumerate(scenario.get("models", [])):
      check_model(
         errors,
         model,
         model_index,
         seen_model_ids,
         seen_element_ids,
         seen_matlab_symbols,
      )

   for relation_index, relation in enumerate(scenario.get("consistency_relations", [])):
      check_relation(errors, relation, relation_index, seen_relation_ids, seen_element_ids)

   return errors


def check_scenario_identity(errors: list, scenario: dict):
   missing_fields = missing_required_fields(scenario, SCENARIO_REQUIRED_FIELDS)
   if missing_fields:
      errors.append(f"Scenario is missing the following required fields: {','.join(missing_fields)}")
      return

   add_pattern_error(errors, "Scenario ID", scenario["scenario_id"], SCENARIO_ID_PATTERN, SCENARIO_ID_REGEX)


def check_model(
   errors: list,
   model: dict,
   model_index: int,
   seen_model_ids: set,
   seen_element_ids: set,
   seen_matlab_symbols: set,
):
   check_unique_id(
      errors,
      value=model.get("id"),
      seen_ids=seen_model_ids,
      missing_message=f"Model {model_index} does not have an ID",
      duplicate_message=f"Model {model_index} does not have a unique ID",
      pattern_label=f"Model {model_index} ID",
   )

   missing_fields = missing_required_fields(model, MODEL_REQUIRED_FIELDS)
   if "name" in missing_fields:
      errors.append(f"Model {model_index} does not have a name")

   elements = model.get("elements", [])
   if not elements:
      errors.append(f"Model {model_index} does not have any elements")

   for element_index, element in enumerate(elements):
      check_element(errors, element, model_index, element_index, seen_element_ids, seen_matlab_symbols)


def check_element(
   errors: list,
   element: dict,
   model_index: int,
   element_index: int,
   seen_element_ids: set,
   seen_matlab_symbols: set,
):
   element_label = f"Element {element_index} of model {model_index}"
   missing_fields = missing_required_fields(element, ELEMENT_REQUIRED_FIELDS)

   if missing_fields:
      errors.append(f"{element_label} is missing the following required fields: {', '.join(missing_fields)}")

   if "id" in element:
      check_unique_id(
         errors,
         value=element["id"],
         seen_ids=seen_element_ids,
         missing_message=f"{element_label} does not have an ID",
         duplicate_message=f"{element_label} does not have a unique ID",
         pattern_label=f"{element_label} ID",
      )

   if "symbol" in element:
      add_matlab_identifier_error(errors, f"{element_label} symbol", element["symbol"])
      add_matlab_identifier_collision_error(errors, seen_matlab_symbols, f"{element_label} symbol", element["symbol"])

   if "uncertainty" not in element and "fixed_value" not in element:
      errors.append(f"{element_label} has neither uncertainty nor a fixed value")

   if "uncertainty" in element:
      check_uncertainty(errors, element["uncertainty"], model_index, element_index)


def check_uncertainty(errors: list, uncertainty: dict, model_index: int, element_index: int):
   label = f"Element {element_index} of model {model_index}"
   uncertainty_type = uncertainty["type"]

   if uncertainty_type == INTERVAL:
      check_interval_uncertainty(errors, uncertainty, label)
   elif uncertainty_type == PROBABILISTIC:
      check_probabilistic_uncertainty(errors, uncertainty, label)
   else:
      check_binary_uncertainty(errors, uncertainty, label)


def check_interval_uncertainty(errors: list, uncertainty: dict, label: str):
   if "min" not in uncertainty or "max" not in uncertainty:
      errors.append(f"{label} has interval uncertainty but is missing min or max")
   elif uncertainty["min"] >= uncertainty["max"]:
      errors.append(f"{label} has interval uncertainty but min is not smaller than max")


def check_probabilistic_uncertainty(errors: list, uncertainty: dict, label: str):
   if "mean" not in uncertainty or "std" not in uncertainty:
      errors.append(f"{label} has probabilistic uncertainty but is missing mean or std")
   elif uncertainty["std"] <= 0:
      errors.append(f"{label} has probabilistic uncertainty but std is not greater than 0")


def check_binary_uncertainty(errors: list, uncertainty: dict, label: str):
   if "option_0" not in uncertainty or "option_1" not in uncertainty:
      errors.append(f"{label} has binary uncertainty but the options are not specified")
   elif uncertainty["option_0"] == uncertainty["option_1"]:
      errors.append(f"{label} has binary uncertainty but the options are the same")


def check_relation(
   errors: list,
   relation: dict,
   relation_index: int,
   seen_relation_ids: set,
   seen_element_ids: set,
):
   missing_fields = missing_required_fields(relation, RELATION_REQUIRED_FIELDS)
   if missing_fields:
      errors.append(f"Relation {relation_index} is missing the following required fields: {', '.join(missing_fields)}")

   if "id" in relation:
      check_unique_id(
         errors,
         value=relation["id"],
         seen_ids=seen_relation_ids,
         missing_message=f"Relation {relation_index} does not have an ID",
         duplicate_message=f"Relation {relation_index} does not have a unique ID",
         pattern_label=f"Relation {relation_index} ID",
      )

   references_invalid_element = (
      "from_element_id" in relation and relation["from_element_id"] not in seen_element_ids
      or "to_element_id" in relation and relation["to_element_id"] not in seen_element_ids
   )
   if references_invalid_element:
      errors.append(f"Relation {relation_index} does not reference valid elements")


def check_unique_id(
   errors: list,
   value,
   seen_ids: set,
   missing_message: str,
   duplicate_message: str,
   pattern_label: str,
):
   if value is None:
      errors.append(missing_message)
      return

   if value in seen_ids:
      errors.append(duplicate_message)
   else:
      add_pattern_error(errors, pattern_label, value, GENERIC_ID_PATTERN, GENERIC_ID_REGEX)
      seen_ids.add(value)


def missing_required_fields(data: dict, fields: list) -> list:
   return [field for field in fields if field not in data]


def add_pattern_error(errors: list, label: str, value, pattern, pattern_text: str):
   if pattern.fullmatch(str(value)):
      return

   errors.append(f"{label} must match pattern {pattern_text}")


def is_valid_matlab_identifier(value) -> bool:
   value = str(value)
   return bool(MATLAB_IDENTIFIER_PATTERN.fullmatch(value)) and value not in MATLAB_KEYWORDS


def add_matlab_identifier_error(errors: list, label: str, value):
   if is_valid_matlab_identifier(value):
      return

   errors.append(
      f"{label} must be a valid MATLAB identifier. Use pattern {MATLAB_IDENTIFIER_REGEX} and avoid MATLAB keywords."
   )


def add_matlab_identifier_collision_error(errors: list, used_names: set, label: str, value):
   if value in used_names:
      errors.append(f"{label} conflicts with another MATLAB identifier: '{value}'")

   used_names.add(value)


def check_completeness_rules(scenario: dict) -> list:
   ans = []

   if not scenario.get("consistency_relations"):
      ans.append("Scenario does not have any consistency relations")

   for i, relation in enumerate(scenario.get("consistency_relations", [])):
      missing_fields = [
         field for field in RECOMMENDED_RELATION_FIELDS
         if field not in relation
      ]

      if missing_fields:
         ans.append(
            f"Relation {i} is missing recommended UPR fields: {', '.join(missing_fields)}"
         )

   for i, model in enumerate(scenario.get("models", [])):
      for j, element in enumerate(model.get("elements", [])):
         if "uncertainty" not in element:
            continue

         classification = element.get("classification", {})
         missing_fields = [
            field for field in RECOMMENDED_CLASSIFICATION_FIELDS
            if field not in classification
         ]

         if missing_fields:
            ans.append(
               f"Element {j} of model {i} is missing recommended classification fields: {', '.join(missing_fields)}"
            )

   return ans


def check_cross_field_rules(scenario: dict) -> list:
   ans = []

   for i, relation in enumerate(scenario.get("consistency_relations", [])):
      check_relation_endpoints(ans, relation, i)

   for i, model in enumerate(scenario.get("models", [])):
      for j, element in enumerate(model.get("elements", [])):
         if "uncertainty" not in element:
            continue

         uncertainty = element["uncertainty"]
         uncertainty_type = uncertainty["type"]
         classification = element.get("classification", {})

         if (
            classification.get("nature") == "Aleatory"
            and uncertainty_type not in CONTINUOUS_UNCERTAINTY_TYPES
         ):
            ans.append(
               f"Element {j} of model {i} has nature Aleatory but uncertainty type is not interval or probabilistic"
            )

         if (
            classification.get("reducibility_level") == "Fully Reducible"
            and classification.get("nature") != "Epistemic"
         ):
            ans.append(
               f"Element {j} of model {i} is Fully Reducible but nature is not Epistemic"
            )

         if (
            classification.get("risk_type") == "High"
            and classification.get("risk_scale", 0) < 70
         ):
            ans.append(
               f"Element {j} of model {i} has risk type High but risk scale is below 70"
            )

         check_effect_type_consistency(ans, classification, uncertainty_type, i, j)

   return ans


def check_relation_endpoints(warnings: list, relation: dict, relation_index: int):
   from_element_id = relation.get("from_element_id")
   to_element_id = relation.get("to_element_id")

   if from_element_id and from_element_id == to_element_id:
      warnings.append(
         f"Relation {relation_index} references the same element as both source and target"
      )


def check_effect_type_consistency(
   warnings: list,
   classification: dict,
   uncertainty_type: str,
   model_index: int,
   element_index: int,
):
   effect_type = classification.get("effect_type")
   if not effect_type:
      return

   if effect_type in UNSUPPORTED_EFFECT_TYPES:
      warnings.append(
         f"Element {element_index} of model {model_index} has effect type {effect_type}, "
         "but the current generator does not support a separate discrete probabilistic uncertainty representation"
      )
      return

   expected_uncertainty_type = EFFECT_TYPE_TO_UNCERTAINTY_TYPE.get(effect_type)
   if expected_uncertainty_type and uncertainty_type != expected_uncertainty_type:
      warnings.append(
         f"Element {element_index} of model {model_index} has effect type {effect_type}, "
         f"but uncertainty type is {uncertainty_type}; expected {expected_uncertainty_type}"
      )
