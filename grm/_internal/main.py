#!/usr/bin/env python3

import os
import shlex
import subprocess
import sys

from grm._internal.argparser import create_argparser
from grm.path_rules import process_path_rules
from grm.path_rules import process_path_join_rules
from grm.config import load_config


def do_clone(args, unparsed_args):
    config = load_config(args.config)

    target_directory = process_path_rules(config["path_rules"], args.repo)
    target_directory = os.path.join(config["repo_root"], *target_directory)

    if os.path.exists(target_directory):
        if not args.auto_pull:
            sys.exit(
                f"directory {target_directory} already exists, use --auto-pull to pull instead"
            )

        # check it's for the same repo
        try:
            p = subprocess.run(
                ["git", "-C", target_directory, "config", "remote.origin.url"],
                check=True,
                capture_output=True,
                text=True,
            )

            target_directory_repo = p.stdout.strip()

        except subprocess.CalledProcessError as ex:
            sys.exit(f"error while trying to auto-pull {target_directory}: {ex.stderr}")

        if target_directory_repo != args.repo:
            print(f"{target_directory_repo} != {args.repo}", file=sys.stderr)
            sys.exit(
                f"error while trying to auto-pull: a different repository is checked out at {target_directory}"
            )

        subprocess.run(["git", "-C", target_directory, "pull", "--ff-only"])

    else:
        cmd = [
            "git",
            "clone",
            args.repo,
            target_directory,
        ]

        if args.depth is not None:
            if args.depth != -1:
                cmd.append(f"--depth={args.depth}")
        elif config["clone"]["default_depth"] != -1:
            cmd.append(f"--depth={config['clone']['default_depth']}")

        cmd.extend(unparsed_args)
        subprocess.run(cmd)


def do_hub_create(args, unparsed_args):
    config = load_config(args.config)
    repo_root = config["repo_root"]
    hub_cmd = config["hub_cmd"].strip()

    target_directory = process_path_join_rules(
        config["path_join_rules"], os.path.abspath(args.repo)
    )

    if target_directory.startswith(repo_root):
        target_directory = target_directory[len(repo_root) + 1 :]
    print(target_directory)

    cmd = [
        hub_cmd,
        "create",
    ]

    if args.private:
        cmd.append("--private")

    cmd.append(target_directory)
    cmd.extend(unparsed_args)

    print("running:", cmd)
    subprocess.run(shlex.join(cmd), shell=True)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = create_argparser(
        do_clone=do_clone,
        do_hub_create=do_hub_create,
    )

    args, unparsed_args = parser.parse_known_args()

    args.func(args, unparsed_args)


if __name__ == "__main__":
    main()
