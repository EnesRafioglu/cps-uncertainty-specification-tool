```text
scenario
├── scenario_id
├── name
├── description
├── models[]
│   ├── id
│   ├── name
│   ├── type
│   └── elements[]
│       ├── id
│       ├── name
│       ├── symbol
│       ├── unit
│       ├── description
│       ├── uncertainty
│       │   ├── interval
│       │   │   ├── type = "interval"
│       │   │   ├── source
│       │   │   ├── min
│       │   │   └── max
│       │   ├── probabilistic
│       │   │   ├── type = "probabilistic"
│       │   │   ├── source
│       │   │   ├── distribution = "gaussian"
│       │   │   ├── mean
│       │   │   └── std
│       │   └── binary
│       │       ├── type = "binary"
│       │       ├── source
│       │       ├── option_0
│       │       └── option_1
│       ├── fixed_value
│       └── classification
│           ├── development_phase
│           ├── reducibility_level
│           ├── nature
│           ├── kind
│           ├── atomic_component_type
│           ├── physical_component_type
│           ├── model_component_type
│           ├── composite_type
│           ├── autonomy_type
│           ├── location_type
│           ├── model_uncertainty_type
│           ├── source_type
│           ├── pattern_type
│           ├── perspective_type
│           ├── effect_type
│           ├── level_type
│           ├── risk_type
│           └── risk_scale
└── consistency_relations[]
    ├── id
    ├── from_element_id
    ├── to_element_id
    ├── operator
    ├── expression
    ├── upr_type
    ├── upr_sigma
    └── upr_description
```