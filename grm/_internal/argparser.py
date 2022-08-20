import argparse
import os


def create_argparser(do_clone):
    # create the top-level parser
    parser = argparse.ArgumentParser(prog="grm", allow_abbrev=False)
    parser.add_argument(
        "--config",
        help="Config file location",
        default=os.path.expanduser("~/.config/grm/grm.yaml"),
    )

    subparsers = parser.add_subparsers(help="sub-command help")

    sp_clone = subparsers.add_parser(
        "clone",
        help="Clones a repository into the repo root, applying any "
        + "configured path rules",
    )
    sp_clone.add_argument("--depth", type=int, help="Only clone to this depth")
    sp_clone.add_argument("repo", help="Repo to clone")

    sp_clone.set_defaults(func=do_clone)

    return parser
