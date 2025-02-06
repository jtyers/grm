#!/usr/bin/env python3

import os
import shlex
import shutil
import subprocess
import sys
import click

from grm._internal.argparser import create_argparser
from grm.path_rules import process_path_rules
from grm.path_rules import process_path_join_rules
from grm.config import load_config


@click.group
def main():
    pass


@main.command
@click.option("--depth")
@click.option(
    "--auto-pull/--no-auto-pull",
    help="If specified and the local repo already exists, pull the latest commits from the default origin instead",
)
@click.option(
    "--config",
    default=os.path.expanduser("~/.config/grm/grm.yaml"),
)
@click.argument("repo")
def clone(config, auto_pull, depth, repo):
    config = load_config(config)

    target_directory = process_path_rules(config["path_rules"], repo)
    target_directory = os.path.join(config["repo_root"], *target_directory)

    if os.path.exists(target_directory):
        if not auto_pull:
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

        if target_directory_repo != repo:
            print(f"{target_directory_repo} != {repo}", file=sys.stderr)
            sys.exit(
                f"error while trying to auto-pull: a different repository is checked out at {target_directory}"
            )

        subprocess.run(["git", "-C", target_directory, "pull", "--ff-only"])

    else:
        cmd = [
            "git",
            "clone",
            repo,
            target_directory,
        ]

        if depth is not None:
            if depth != -1:
                cmd.append(f"--depth={depth}")
        elif config["clone"]["default_depth"] != -1:
            cmd.append(f"--depth={config['clone']['default_depth']}")

        #cmd.extend(unparsed_args)
        subprocess.run(cmd)


@main.command
@click.option("--private/--no-private", "-p/-P", type=bool, required=True)
@click.option(
    "--config",
    default=os.path.expanduser("~/.config/grm/grm.yaml"),
)
@click.argument("repo")
def create(repo, config, private):
    config = load_config(config)
    repo_root = config["repo_root"]
    hub_cmd = os.path.expandvars(
        os.path.expanduser(config.get("hub_cmd", "hub").strip())
    )

    target_directory = process_path_join_rules(
        config["path_join_rules"], os.path.abspath(repo)
    )

    if not target_directory.startswith(repo_root):
        print(
            f"must be in repo_root ({repo_root.replace(os.environ['HOME'], '~')}) to use this command",
            file=sys.stderr,
        )
        sys.exit(1)

    if not (os.path.exists(hub_cmd) or shutil.which(hub_cmd)):
        print(
            f"cannot find hub command '{hub_cmd}'",
            file=sys.stderr,
        )
        sys.exit(1)

    target_directory = target_directory[len(repo_root) + 1 :]

    cmd = [
        hub_cmd,
        "create",
    ]

    if private:
        print("creating private Github repository ", target_directory)
        cmd.append("--private")

    else:
        print("creating public Github repository ", target_directory)

    cmd.append(target_directory)
    #cmd.extend(unparsed_args)

    subprocess.run(shlex.join(cmd), shell=True)


@main.command
def update():
    raise NotImplementedError()


if __name__ == "__main__":
    main()
