import os
import yaml

from grm.constants import DEFAULTS
from grm.constants import DEFAULT_PATH_RULES
from grm.util import deep_merge_dicts


def load_config(config_file):
    result = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            result = yaml.safe_load(f)

    result = deep_merge_dicts(result, DEFAULTS)

    if result["include_default_path_rules"]:
        result["path_rules"] = DEFAULT_PATH_RULES + result["path_rules"]

    return result
