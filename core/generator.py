
def generate_matlab_output(scenario: dict) -> str:
   lines = [
      f"% Scenario: {scenario["name"]}",
      f"% Scenario ID: {scenario["scenario_id"]}",
      "%",
      "% Dependencies:",
      "% - CORA for continuous zonotopes: zonotope(...)",
      "% - https://github.com/aalanwar/Logical-Zonotope for logical zonotopes: logicalZonotope(...)",
   ]

   for model in scenario["models"]:
      lines.append(f"\n% Model ID: {model["id"]}")
      lines.append(f"% Model name: {model["name"]}\n")

      has_uncertain_element = False

      for element in model["elements"]:
         lines.append(f"% Element: {element["name"]}")
         lines.append(f"% Symbol: {element["symbol"]}")
         lines.append(f"% Unit: {element["unit"]}")

         if "uncertainty" in element:
            has_uncertain_element = True
            uncertainty = element["uncertainty"]
            u_type = uncertainty["type"]
            lines.append(f"% Uncertainty type: {u_type}\n")
            if u_type == "interval":
               mn, mx = uncertainty["min"], uncertainty["max"]
               symbol = element["symbol"]
               lines.append(f"{symbol}_min = {mn};")
               lines.append(f"{symbol}_max = {mx};\n")
               lines.extend(make_zonotope(symbol, f"({symbol}_min + {symbol}_max) / 2", f"({symbol}_max - {symbol}_min) / 2"))
            elif u_type == "probabilistic":
               mean, std = uncertainty["mean"], uncertainty["std"]
               symbol = element["symbol"]
               lines.append("% Probabilistic uncertainty is converted into a 95% confidence interval.")
               lines.append(f"{symbol}_mean = {mean};")
               lines.append(f"{symbol}_std = {std};")
               lines.append(f"{symbol}_confidence_factor = 1.96;\n")
               lines.extend(make_zonotope(symbol, f"{symbol}_mean", f"{symbol}_confidence_factor * {symbol}_std"))
            else:
               option_0, option_1 = uncertainty["option_0"], uncertainty["option_1"]
               symbol = element["symbol"]
               lines.append(f"% Options: 0 = {option_0}, 1 = {option_1}")
               lines.extend(make_logical_zonotope(symbol))

      if not has_uncertain_element:
         lines.append("% Model has no uncertain elements.")

   return "\n".join(lines)


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
