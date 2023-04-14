import re


def __process_split_path_rule__(path_rule, result):
    # Processes a "type: split" path rule, where we split the path on a
    # string (currently exact_match supported only), and then optionally
    # insert some other string at the split-point.
    if "exact_match" in path_rule:
        new_result = []
        for r in result:
            s = r.split(path_rule["exact_match"], maxsplit=path_rule.get("limit", -1))

            if path_rule.get("insert", None) and len(s) > 1:
                # If the path_rule says to insert a string where the
                # splits occurred, we need some guesswork to workout
                # where the splits did indeed occur.
                #
                # To do this we insert at odd-number indexes until the
                # penultimate item is the insert value (showing we've
                # reached the last split point in the string).
                count = 1
                while s[-2] != path_rule["insert"]:
                    s.insert(count, path_rule["insert"])
                    count += 2

            new_result.extend(s)

        return new_result

    else:
        raise ValueError(
            'path_rules items where type == "split" must'
            + " have an exact_match specified"
        )


def __process_path_join_rule__(path_join_rule: dict, result: list[str]) -> list[str]:
    # Processes a "type: split" path rule, but in reverse. Instead of
    # splitting, then inserting, we split on the insertion, then join
    # using the split exact_match.
    if "exact_match" in path_join_rule:
        new_result: list[str] = []
        for r in result:
            new_result.append(
                r.replace(path_join_rule["exact_match"], path_join_rule["replace"])
            )

        return new_result

    else:
        raise ValueError(
            'path_rules items where type == "split" must'
            + " have an exact_match specified"
        )


def __process_delete_path_rule__(path_rule, result):
    new_result = list(result)

    if "regex" in path_rule:
        regex = re.compile(path_rule["regex"])

        m = regex.search(new_result[0])
        if m:
            new_result[0] = new_result[0][0 : m.start()] + new_result[0][m.end() :]

        return new_result

    else:
        raise ValueError(
            'path_rules items where type == "delete" must have a regex' " specified"
        )


def process_path_rules(path_rules: list[dict], input_path: str) -> list[str]:
    # print("process_path_rules", input_path)
    result = [input_path]
    for path_rule in path_rules:
        # print("> path_rule", path_rule)
        if path_rule["type"] == "split":
            result = __process_split_path_rule__(path_rule, result)

        elif path_rule["type"] == "delete":
            result = __process_delete_path_rule__(path_rule, result)

        else:
            raise ValueError(f'unknown path_rule type {path_rule["type"]}')

        # print("> result =", result)

    return result


def process_path_join_rules(path_join_rules: list[dict], input_path: str) -> list[str]:
    print("process_path_rules_reversed", input_path)
    result = [input_path]
    for path_join_rule in path_join_rules:
        print("> path_join_rule", path_join_rule)
        result = __process_path_join_rule__(path_join_rule, result)

        print("> result =", result)

    return "".join(result)
