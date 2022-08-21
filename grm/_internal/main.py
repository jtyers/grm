#!/usr/bin/env python3

import os
import subprocess
import sys

from grm._internal.argparser import create_argparser
from grm.path_rules import process_path_rules
from grm.config import load_config


def do_clone(args, unparsed_args):
    config = load_config(args.config)

    target_directory = process_path_rules(config["path_rules"], args.repo)
    target_directory = os.path.join(config["repo_root"], *target_directory)

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

    print(cmd)

    subprocess.run(cmd)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = create_argparser(
        do_clone=do_clone,
    )

    args, unparsed_args = parser.parse_known_args()

    print(args)
    print(unparsed_args)

    args.func(args, unparsed_args)


if __name__ == "__main__":
    main()
