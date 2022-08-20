import os

DEFAULT_PATH_RULES = [
    {
        "type": "delete",
        "regex": "^https://[^/]+/",
    },
    {
        "type": "delete",
        "regex": "^.*:",
    },
    {
        "type": "delete",
        "regex": ".git$",
    },
    {
        "type": "split",
        "exact_match": ":",
        "limit": 1,
    },
    {
        "type": "split",
        "exact_match": "/",
    },
    {
        "type": "split",
        "exact_match": "-tf-modules-",
        "insert": "tf-modules",
    },
    {
        "type": "split",
        "exact_match": "-tf-live",
        "insert": "tf-live",
    },
]

DEFAULTS = {
    "repo_root": os.path.expanduser("~/git"),
    "clone": {
        "default_depth": 1,
    },
    "path_rules": [],
    "include_default_path_rules": True,
}
