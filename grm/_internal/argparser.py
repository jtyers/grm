import argparse
import os


def create_argparser(do_clone, do_hub_create):
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
    sp_clone.add_argument(
        "--auto-pull",
        action="store_true",
        help="If specified and the local repo already exists, pull the latest commits from the default origin instead",
    )
    sp_clone.add_argument("repo", help="Repo to clone")

    sp_clone.set_defaults(func=do_clone)

    sp_hub_create = subparsers.add_parser(
        "hub-create",
        help="Creates a repository in Github, using path rules to construct "
        "the repo path",
    )
    sp_hub_create.add_argument(
        "-p",
        "--private",
        action="store_true",
        help="Create a private repository",
    )
    sp_hub_create.add_argument(
        "repo",
        default=os.getcwd(),
        help="Path to repo to create",
    )

    sp_hub_create.set_defaults(func=do_hub_create)

    return parser
