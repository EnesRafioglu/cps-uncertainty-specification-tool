from collections import defaultdict

from core.constants import NUMERIC_FIELDS


def build_scenario_from_form(form_data) -> dict:
    paths = form_data_to_paths(form_data)
    return build_nested_value(paths).get("scenario", {})


def form_data_to_paths(form_data):
    paths = []
    for key, value in form_data.items():
        if value == "":
            continue

        path = key.split(".")
        field_name = path[-1]
        path.append(convert_value(field_name, value))
        paths.append(path)
    
    return paths


def convert_value(field, value):
    if field not in NUMERIC_FIELDS or value == "":
        return value

    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def paths_start_with_index(paths):
    for path in paths:
        if path and path[0].isdigit():
            return True 
    
    return False


def build_nested_value(paths):
    if paths_start_with_index(paths):
        item_count = max(int(path[0]) for path in paths) + 1
        result = [None] * item_count
        grouped_paths = [[] for _ in range(item_count)]

        for path in paths:
            if len(path) == 2:
                result[int(path[0])] = path[1]
            else:
                grouped_paths[int(path[0])].append(path[1:])

        for i in range(item_count):
            if grouped_paths[i]:
                result[i] = build_nested_value(grouped_paths[i])
        
        return result

    result = {}
    grouped_paths = defaultdict(list)

    for path in paths:
        if not path:
            continue

        if len(path) == 2:
            result[path[0]] = path[1]
        else:
            grouped_paths[path[0]].append(path[1:])

    for key, value in grouped_paths.items():
        result[key] = build_nested_value(value)

    return result
