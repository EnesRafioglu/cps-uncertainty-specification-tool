% Scenario: Autonomous Warehouse Robot
% Scenario ID: warehouse_robot_01
%
% Dependencies:
% - CORA for continuous zonotopes: zonotope(...)
% - https://github.com/aalanwar/Logical-Zonotope for logical zonotopes: logicalZonotope(...)

% Model ID: thermal_model
% Model name: Thermal Simulation Model

% Element: Motor Temperature
% Symbol: T_motor
% Unit: degC
% Uncertainty type: interval

T_motor_min = 72;
T_motor_max = 91;

T_motor_c = (T_motor_min + T_motor_max) / 2;
T_motor_G = (T_motor_max - T_motor_min) / 2;
T_motor_Z = zonotope([T_motor_c, T_motor_G]);

% Element: Ambient Temperature
% Symbol: T_ambient
% Unit: degC
% Uncertainty type: probabilistic

% Probabilistic uncertainty is converted into a 95% confidence interval.
T_ambient_mean = 24;
T_ambient_std = 2.5;
T_ambient_confidence_factor = 1.96;

T_ambient_c = T_ambient_mean;
T_ambient_G = T_ambient_confidence_factor * T_ambient_std;
T_ambient_Z = zonotope([T_ambient_c, T_ambient_G]);

% Element: Motor Temperature Limit
% Symbol: T_limit
% Unit: degC
% Fixed/reference value

T_limit = 95;

% Joint continuous zonotope for model 1
% Independent continuous dimensions are combined with a diagonal generator matrix.
% Continuous and binary dimensions are kept separate.
% Dimension order: T_motor, T_ambient
model_1_continuous_c = [T_motor_c; T_ambient_c];
model_1_continuous_G = diag([T_motor_G; T_ambient_G]);
model_1_continuous_Z = zonotope([model_1_continuous_c, model_1_continuous_G]);

% Model ID: energy_model
% Model name: Battery Performance Model

% Element: Battery State of Charge
% Symbol: soc
% Unit: percent
% Uncertainty type: probabilistic

% Probabilistic uncertainty is converted into a 95% confidence interval.
soc_mean = 68;
soc_std = 4;
soc_confidence_factor = 1.96;

soc_c = soc_mean;
soc_G = soc_confidence_factor * soc_std;
soc_Z = zonotope([soc_c, soc_G]);

% Element: Payload Mass
% Symbol: payload_mass
% Unit: kg
% Uncertainty type: interval

payload_mass_min = 8;
payload_mass_max = 15;

payload_mass_c = (payload_mass_min + payload_mass_max) / 2;
payload_mass_G = (payload_mass_max - payload_mass_min) / 2;
payload_mass_Z = zonotope([payload_mass_c, payload_mass_G]);

% Element: Minimum Required State of Charge
% Symbol: soc_min
% Unit: percent
% Fixed/reference value

soc_min = 35;

% Joint continuous zonotope for model 2
% Independent continuous dimensions are combined with a diagonal generator matrix.
% Continuous and binary dimensions are kept separate.
% Dimension order: soc, payload_mass
model_2_continuous_c = [soc_c; payload_mass_c];
model_2_continuous_G = diag([soc_G; payload_mass_G]);
model_2_continuous_Z = zonotope([model_2_continuous_c, model_2_continuous_G]);

% Model ID: perception_control_model
% Model name: Perception and Control Model

% Element: Perception Quality
% Symbol: q_perception
% Unit: score
% Uncertainty type: probabilistic

% Probabilistic uncertainty is converted into a 95% confidence interval.
q_perception_mean = 0.88;
q_perception_std = 0.04;
q_perception_confidence_factor = 1.96;

q_perception_c = q_perception_mean;
q_perception_G = q_perception_confidence_factor * q_perception_std;
q_perception_Z = zonotope([q_perception_c, q_perception_G]);

% Element: Controller Mode
% Symbol: controller_mode
% Unit: mode
% Uncertainty type: binary

% Options: 0 = nominal_mode, 1 = cautious_mode
controller_mode_c_L = 0;
controller_mode_G_L = {1};
controller_mode_Z = logicalZonotope(controller_mode_c_L, controller_mode_G_L);

% Element: Emergency Stop Availability
% Symbol: emergency_stop
% Unit: boolean
% Uncertainty type: binary

% Options: 0 = not_available, 1 = available
emergency_stop_c_L = 0;
emergency_stop_G_L = {1};
emergency_stop_Z = logicalZonotope(emergency_stop_c_L, emergency_stop_G_L);

% Element: Minimum Perception Quality
% Symbol: q_min
% Unit: score
% Fixed/reference value

q_min = 0.75;

% Joint logical zonotope for model 3
% Binary dimensions are kept separate from continuous dimensions.
% Independent binary choices use one generator cell per identity column.
% Dimension order: controller_mode, emergency_stop
model_3_binary_c_L = zeros(2, 1);
model_3_binary_G_L = num2cell(logical(eye(2)), 1);
model_3_binary_Z = logicalZonotope(model_3_binary_c_L, model_3_binary_G_L);

%% Consistency relations
% cr_temperature_limit [constraint_based]: T_motor <= T_limit
% cr_soc_requirement [constraint_based]: soc >= soc_min
% cr_perception_threshold [constraint_based]: q_perception >= q_min
% cr_emergency_guard [guarded]: controller_mode = cautious_mode if emergency_stop = available
