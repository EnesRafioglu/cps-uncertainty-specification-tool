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
   ans = []
   model_ids, element_ids, relation_ids = set(), set(), set()

   missing_scenario_fields = [field for field in ["scenario_id", "name"] if field not in scenario]
   if missing_scenario_fields:
      ans.append(f"Scenario is missing the following required fields: {','.join(missing_scenario_fields)}")

   if not scenario.get("models"):
      ans.append("Scenario does not have any models")

   for i, model in enumerate(scenario.get("models", [])):
      if "id" not in model:
         ans.append(f"Model {i} does not have an ID")
      
      elif model["id"] in model_ids:
         ans.append(f"Model {i} does not have a unique ID")

      else: 
         model_ids.add(model["id"])

      if "name" not in model:
         ans.append(f"Model {i} does not have a name")

      if not model.get("elements"):
         ans.append(f"Model {i} does not have any elements")

      uncertain_element_count = 0
      for j, element in enumerate(model.get("elements", [])):

         missing_fields = [field for field in ["id", "name", "symbol", "unit"] if field not in element]
         if missing_fields:
            ans.append(f"Element {j} of model {i} is missing the following required fields: {", ".join(missing_fields)}")
         
         if "id" in element:
            if element["id"] in element_ids:
               ans.append(f"Element {j} of model {i} does not have a unique ID")
            
            element_ids.add(element["id"])
         
         if "uncertainty" not in element and "fixed_value" not in element:
            ans.append(f"Element {j} of model {i} has neither uncertainty nor a fixed value")
         
         if "uncertainty" in element:
            uncertain_element_count += 1
            uncertainty = element["uncertainty"]
            uncertainty_type = uncertainty["type"]

            if uncertainty_type == "interval":
               if "min" not in uncertainty or "max" not in uncertainty:
                  ans.append(f"Element {j} of model {i} has interval uncertainty but is missing min or max")
               
               elif uncertainty["min"] >= uncertainty["max"]:
                  ans.append(f"Element {j} of model {i} has interval uncertainty but min is not smaller than max")
            
            elif uncertainty_type == "probabilistic":
               if "mean" not in uncertainty or "std" not in uncertainty:
                  ans.append(f"Element {j} of model {i} has probabilistic uncertainty but is missing mean or std")
               
               elif uncertainty["std"] <= 0:
                  ans.append(f"Element {j} of model {i} has probabilistic uncertainty but std is not greater than 0")
            
            else:
               if "option_0" not in uncertainty or "option_1" not in uncertainty:
                  ans.append(f"Element {j} of model {i} has binary uncertainty but the options are not specified")
               
               elif uncertainty["option_0"] == uncertainty["option_1"]:
                  ans.append(f"Element {j} of model {i} has binary uncertainty but the options are the same")

      if uncertain_element_count > 1:
         ans.append(f"More than 1 uncertain element per model is currently not supported")

   for i, relation in enumerate(scenario.get("consistency_relations", [])):
      missing_fields = [field for field in ["id", "from_element_id", "to_element_id", "expression"] if field not in relation]
      if missing_fields:
         ans.append(f"Relation {i} is missing the following required fields: {", ".join(missing_fields)}")
      
      if "id" in relation:
         if relation["id"] in relation_ids:
            ans.append(f"Relation {i} does not have a unique ID")
         
         relation_ids.add(relation["id"])
      
      if (
         "from_element_id" in relation and relation["from_element_id"] not in element_ids
         or "to_element_id" in relation and relation["to_element_id"] not in element_ids
      ):
         ans.append(f"Relation {i} does not reference valid elements")

   return ans


def check_completeness_rules(scenario: dict) -> list:
   ans = []

   if not scenario.get("consistency_relations"):
      ans.append("Scenario does not have any consistency relations")

   for i, model in enumerate(scenario.get("models", [])):
      for j, element in enumerate(model.get("elements", [])):
         if "uncertainty" not in element:
            continue

         classification = element.get("classification", {})
         missing_fields = [
            field for field in ["development_phase", "reducibility_level"]
            if field not in classification
         ]

         if missing_fields:
            ans.append(
               f"Element {j} of model {i} is missing recommended classification fields: {', '.join(missing_fields)}"
            )

   return ans


def check_cross_field_rules(scenario: dict) -> list:
   ans = []

   for i, model in enumerate(scenario.get("models", [])):
      for j, element in enumerate(model.get("elements", [])):
         if "uncertainty" not in element:
            continue

         uncertainty = element["uncertainty"]
         uncertainty_type = uncertainty["type"]
         classification = element.get("classification", {})

         if (
            classification.get("nature") == "Aleatory"
            and uncertainty_type not in ["interval", "probabilistic"]
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

   return ans
         