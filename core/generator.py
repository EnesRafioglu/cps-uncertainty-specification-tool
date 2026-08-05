from core.constants import BINARY, CONTINUOUS_UNCERTAINTY_TYPES, INTERVAL, PROBABILISTIC


def generate_matlab_output(scenario: dict) -> str:
   lines = make_header(scenario)

   for model_index, model in enumerate(scenario["models"], start=1):
      lines.extend(make_model_output(model_index, model))

   lines.extend(make_consistency_relation_comments(scenario.get("consistency_relations", [])))

   return "\n".join(lines)


def make_header(scenario: dict) -> list:
   return [
      f"% Scenario: {scenario["name"]}",
      f"% Scenario ID: {scenario["scenario_id"]}",
      "%",
      "% Dependencies:",
      "% - CORA for continuous zonotopes: zonotope(...)",
      "% - https://github.com/aalanwar/Logical-Zonotope for logical zonotopes: logicalZonotope(...)",
   ]


def make_model_output(model_index: int, model: dict) -> list:
   lines = [
      f"\n% Model ID: {model["id"]}",
      f"% Model name: {model["name"]}",
   ]

   continuous_symbols = []
   binary_symbols = []

   for element in model["elements"]:
      uncertainty_type = add_element_output(lines, element)

      if uncertainty_type in CONTINUOUS_UNCERTAINTY_TYPES:
         continuous_symbols.append(element["symbol"])
      elif uncertainty_type == BINARY:
         binary_symbols.append(element["symbol"])

   lines.extend(make_joint_continuous_zonotope(model_index, continuous_symbols))
   lines.extend(make_joint_logical_zonotope(model_index, binary_symbols))

   return lines


def make_consistency_relation_comments(relations: list) -> list:
   if not relations:
      return []

   lines = ["\n%% Consistency relations"]
   for relation in relations:
      relation_id = relation["id"]
      upr_type = relation["upr_type"]
      expression = relation["expression"]
      lines.append(f"% {relation_id} [{upr_type}]: {expression}")

   return lines


def add_element_output(lines: list, element: dict):
   lines.append(f"\n% Element: {element["name"]}")
   lines.append(f"% Symbol: {element["symbol"]}")
   lines.append(f"% Unit: {element["unit"]}")

   if "uncertainty" in element:
      uncertainty = element["uncertainty"]
      uncertainty_type = uncertainty["type"]
      lines.append(f"% Uncertainty type: {uncertainty_type}\n")

      if uncertainty_type == INTERVAL:
         lines.extend(make_interval_zonotope(element, uncertainty))
      elif uncertainty_type == PROBABILISTIC:
         lines.extend(make_probabilistic_zonotope(element, uncertainty))
      else:
         lines.extend(make_binary_logical_zonotope(element, uncertainty))

      return uncertainty_type

   if "fixed_value" in element:
      lines.extend(make_fixed_value(element))

   return None


def make_interval_zonotope(element: dict, uncertainty: dict) -> list:
   symbol = element["symbol"]
   return [
      f"{symbol}_min = {uncertainty["min"]};",
      f"{symbol}_max = {uncertainty["max"]};\n",
      *make_zonotope(symbol, f"({symbol}_min + {symbol}_max) / 2", f"({symbol}_max - {symbol}_min) / 2"),
   ]


def make_probabilistic_zonotope(element: dict, uncertainty: dict) -> list:
   symbol = element["symbol"]
   return [
      "% Probabilistic uncertainty is converted into a 95% confidence interval.",
      f"{symbol}_mean = {uncertainty["mean"]};",
      f"{symbol}_std = {uncertainty["std"]};",
      f"{symbol}_confidence_factor = 1.96;\n",
      *make_zonotope(symbol, f"{symbol}_mean", f"{symbol}_confidence_factor * {symbol}_std"),
   ]


def make_binary_logical_zonotope(element: dict, uncertainty: dict) -> list:
   symbol = element["symbol"]
   return [
      f"% Options: 0 = {uncertainty["option_0"]}, 1 = {uncertainty["option_1"]}",
      *make_logical_zonotope(symbol),
   ]


def make_fixed_value(element: dict) -> list:
   symbol = element["symbol"]
   return [
      "% Fixed/reference value\n",
      f"{symbol} = {element["fixed_value"]};",
   ]


def make_zonotope(symbol: str, center: str, generator: str) -> list:
   return [
      f"{symbol}_c = {center};",
      f"{symbol}_G = {generator};",
      f"{symbol}_Z = zonotope([{symbol}_c, {symbol}_G]);",
   ]


def make_logical_zonotope(symbol: str) -> list:
   return [
      f"{symbol}_c_L = 0;",
      f"{symbol}_G_L = {{1}};",
      f"{symbol}_Z = logicalZonotope({symbol}_c_L, {symbol}_G_L);",
   ]


def make_joint_continuous_zonotope(model_index: int, symbols: list) -> list:
   if len(symbols) <= 1:
      return []

   base_name = f"model_{model_index}_continuous"
   center_entries = "; ".join(f"{symbol}_c" for symbol in symbols)
   generator_entries = "; ".join(f"{symbol}_G" for symbol in symbols)

   return [
      f"\n% Joint continuous zonotope for model {model_index}",
      "% Independent continuous dimensions are combined with a diagonal generator matrix.",
      "% Continuous and binary dimensions are kept separate.",
      f"% Dimension order: {', '.join(symbols)}",
      f"{base_name}_c = [{center_entries}];",
      f"{base_name}_G = diag([{generator_entries}]);",
      f"{base_name}_Z = zonotope([{base_name}_c, {base_name}_G]);",
   ]


def make_joint_logical_zonotope(model_index: int, symbols: list) -> list:
   if len(symbols) <= 1:
      return []

   base_name = f"model_{model_index}_binary"
   dimension_count = len(symbols)

   return [
      f"\n% Joint logical zonotope for model {model_index}",
      "% Binary dimensions are kept separate from continuous dimensions.",
      "% Independent binary choices use one generator cell per identity column.",
      f"% Dimension order: {', '.join(symbols)}",
      f"{base_name}_c_L = zeros({dimension_count}, 1);",
      f"{base_name}_G_L = num2cell(logical(eye({dimension_count})), 1);",
      f"{base_name}_Z = logicalZonotope({base_name}_c_L, {base_name}_G_L);",
   ]
