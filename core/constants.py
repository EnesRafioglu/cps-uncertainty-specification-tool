INTERVAL = "interval"
PROBABILISTIC = "probabilistic"
BINARY = "binary"

CONTINUOUS_UNCERTAINTY_TYPES = {INTERVAL, PROBABILISTIC}

SCENARIO_ID_REGEX = r"^[a-z0-9_]+$"
GENERIC_ID_REGEX = r"^[A-Za-z0-9_]+$"
MATLAB_IDENTIFIER_REGEX = r"^[A-Za-z][A-Za-z0-9_]*$"

MATLAB_KEYWORDS = {
   "break", "case", "catch", "classdef", "continue", "else", "elseif",
   "end", "for", "function", "global", "if", "otherwise", "parfor",
   "persistent", "return", "spmd", "switch", "try", "while",
}

SCENARIO_REQUIRED_FIELDS = ["scenario_id", "name"]
MODEL_REQUIRED_FIELDS = ["id", "name"]
ELEMENT_REQUIRED_FIELDS = ["id", "name", "symbol", "unit"]
RELATION_REQUIRED_FIELDS = ["id", "from_element_id", "to_element_id", "expression", "upr_type"]

RECOMMENDED_CLASSIFICATION_FIELDS = ["development_phase", "reducibility_level"]
RECOMMENDED_RELATION_FIELDS = ["upr_sigma", "upr_description"]

NUMERIC_FIELDS = {"min", "max", "mean", "std", "risk_scale", "fixed_value"}
