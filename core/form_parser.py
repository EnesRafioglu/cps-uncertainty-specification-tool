from collections import defaultdict


NUMERIC_FIELDS = {"min", "max", "mean", "std", "risk_scale", "fixed_value"}


def build_scenario_from_form(form_data) -> dict:
    paths = convert_form_object_to_list(form_data)
    return build_nested_dict(paths).get("scenario", {})

def convert_form_object_to_list(form_data):
    paths = []
    for key, value in form_data.items():
        if value == "":
            continue

        split_path = key.split('.')
        split_path.append(convert_value(split_path[-1], value))
        paths.append(split_path)
    
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


def has_indices(paths):
    for path in paths:
        if path and path[0].isdigit():
            return True 
    
    return False

def build_nested_dict(paths):

    if has_indices(paths):
        n = max(int(path[0]) for path in paths) + 1
        ans = [None] * n
        split_list = [[] for _ in range(n)]
        for path in paths:
            if len(path) == 2:
                ans[int(path[0])] = path[1]
            
            else:
                split_list[int(path[0])].append(path[1:])

        for i in range(n):
            ans[i] = build_nested_dict(split_list[i])
        
        return ans

    else:

        ans = {}
        split_dict = defaultdict(list)
        for path in paths:
            if not path:
                continue 
            
            if len(path) == 2:
                ans[path[0]] = path[1]

            else:
                split_dict[path[0]].append(path[1:])
        
        
        for key, value in split_dict.items():
            ans[key] = build_nested_dict(value)
        
        return ans
