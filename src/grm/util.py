# https://stackoverflow.com/a/7205107
def deep_merge_dicts(a, b, path=None):
    """Deep-merge two dicts together. b will be merged into a, thus keys
    in b take precedence, and a will be mutated. a is also returned."""
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                deep_merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
