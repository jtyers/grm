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
]

DEFAULTS = {
    "repo_root": os.path.expanduser("~/git"),
    "clone": {
        "default_depth": 1,
    },

    # path_rules should be a list of dicts that look like this:
    #  type: <type>
    #  exact_match: <...>
    #  regex: <...>
    #  limit: <...>
    #  insert: <...>
    #
    "path_rules": [],

    # path_join_rules should be a list of dicts that look like this:
    #  exact_match: <...>
    #  replace: <...>
    #
    "path_join_rules": [],

    "include_default_path_rules": True,
}
