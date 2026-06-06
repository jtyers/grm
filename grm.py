#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["typer", "pyyaml"]
# ///

"""
grm - Git Repository Manager
A single-file executable version created by combining all modules
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import re
import shlex
import shutil
import subprocess
import sys
import yaml
import typer


# === util.py ===
# https://stackoverflow.com/a/7205107
def deep_merge_dicts(a: dict, b: dict, path: Optional[list] = None) -> dict:
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


# === path_rules.py - Dataclasses ===
@dataclass
class SplitPathRule:
    """Path rule that splits a path on an exact match string."""
    exact_match: str
    limit: int = -1
    insert: Optional[str] = None

    @staticmethod
    def from_dict(rule_dict: dict) -> "SplitPathRule":
        """Create a SplitPathRule from a dictionary."""
        return SplitPathRule(**rule_dict)

    def process(self, result: list[str]) -> list[str]:
        """Processes a split path rule, splitting the path on exact_match
        and optionally inserting a string at split points."""
        new_result = []
        for r in result:
            s = r.split(self.exact_match, maxsplit=self.limit)

            if self.insert and len(s) > 1:
                # If the rule says to insert a string where the
                # splits occurred, we need some guesswork to workout
                # where the splits did indeed occur.
                #
                # To do this we insert at odd-number indexes until the
                # penultimate item is the insert value (showing we've
                # reached the last split point in the string).
                count = 1
                while s[-2] != self.insert:
                    s.insert(count, self.insert)
                    count += 2

            new_result.extend(s)

        return new_result


@dataclass
class DeletePathRule:
    """Path rule that deletes a portion of the path matching a regex."""
    regex: str

    @staticmethod
    def from_dict(rule_dict: dict) -> "DeletePathRule":
        """Create a DeletePathRule from a dictionary."""
        return DeletePathRule(**rule_dict)

    def process(self, result: list[str]) -> list[str]:
        """Processes a delete path rule, removing regex matches from the first element."""
        new_result = list(result)
        compiled_regex = re.compile(self.regex)

        m = compiled_regex.search(new_result[0])
        if m:
            new_result[0] = new_result[0][0 : m.start()] + new_result[0][m.end() :]

        return new_result


@dataclass
class ReplacePathJoinRule:
    """Path join rule that reverses split operations by replacing strings.

    Supports two modes:
    - exact_match: Simple string replacement
    - regex: Regular expression matching and replacement

    Exactly one of exact_match or regex must be specified.
    """
    exact_match: Optional[str] = None
    regex: Optional[str] = None
    replace: str = ""

    def __post_init__(self):
        """Validate that exactly one of exact_match or regex is specified."""
        if self.exact_match is not None and self.regex is not None:
            raise ValueError("ReplacePathJoinRule: only one of 'exact_match' or 'regex' can be specified")
        if self.exact_match is None and self.regex is None:
            raise ValueError("ReplacePathJoinRule: one of 'exact_match' or 'regex' must be specified")

    @staticmethod
    def from_dict(rule_dict: dict) -> "ReplacePathJoinRule":
        """Create a ReplacePathJoinRule from a dictionary."""
        return ReplacePathJoinRule(**rule_dict)

    def process(self, result: list[str]) -> list[str]:
        """Processes a path join rule, replacing exact_match or regex pattern with replace."""
        new_result: list[str] = []

        if self.exact_match is not None:
            # Simple string replacement
            for r in result:
                new_result.append(r.replace(self.exact_match, self.replace))
        else:
            # Regex replacement
            compiled_regex = re.compile(self.regex)
            for r in result:
                new_result.append(compiled_regex.sub(self.replace, r))

        return new_result


@dataclass
class DeletePathJoinRule:
    """Path join rule that deletes a portion of the path matching a regex."""
    regex: str

    @staticmethod
    def from_dict(rule_dict: dict) -> "DeletePathJoinRule":
        """Create a DeletePathJoinRule from a dictionary."""
        return DeletePathJoinRule(**rule_dict)

    def process(self, result: list[str]) -> list[str]:
        """Processes a delete path join rule, removing regex matches by substituting with empty string."""
        new_result: list[str] = []
        compiled_regex = re.compile(self.regex)

        for r in result:
            new_result.append(compiled_regex.sub('', r))

        return new_result


# Type aliases for path rules
PathRule = SplitPathRule | DeletePathRule
PathRules = list[PathRule]
PathJoinRule = ReplacePathJoinRule | DeletePathJoinRule
PathJoinRules = list[PathJoinRule]


# === constants.py ===
DEFAULT_PATH_RULES: PathRules = [
    DeletePathRule(regex="^https://[^/]+/"),
    DeletePathRule(regex="^.*:"),
    DeletePathRule(regex=".git$"),
    SplitPathRule(exact_match=":", limit=1),
    SplitPathRule(exact_match="/"),
]


@dataclass
class CloneConfig:
    """Configuration for clone operations."""
    default_depth: int = 1


@dataclass
class Config:
    """Main configuration for grm."""
    repo_root: str
    clone: CloneConfig
    path_rules: PathRules
    path_join_rules: PathJoinRules
    include_default_path_rules: bool = True
    hub_cmd: str = "hub"


DEFAULT_CONFIG = Config(
    repo_root=os.path.expanduser("~/git"),
    clone=CloneConfig(default_depth=1),
    path_rules=[],
    path_join_rules=[],
    include_default_path_rules=True,
    hub_cmd="hub",
)


# === path_rules.py - Processing Functions ===
def process_path_rules(path_rules: PathRules, input_path: str, debug: bool = False) -> list[str]:
    """Process path rules to transform an input path into a list of path components."""
    result = [input_path]

    if debug:
        print(f"\nProcessing path rules for: {input_path}")
        print(f"Initial: {result}")

    for i, path_rule in enumerate(path_rules, 1):
        new_result = path_rule.process(result)
        if debug:
            print(f"  Rule {i} ({path_rule.__class__.__name__}): {path_rule}")
            print(f"    Result: {new_result}")
        result = new_result

    if debug:
        print(f"Final result: {result}\n")

    return result


def process_path_join_rules(path_join_rules: PathJoinRules, input_path: str, debug: bool = False) -> str:
    """Process path join rules to reverse the path transformation."""
    result = [input_path]

    if debug:
        print(f"\nProcessing path join rules for: {input_path}")
        print(f"Initial: {result}")

    for i, path_join_rule in enumerate(path_join_rules, 1):
        new_result = path_join_rule.process(result)
        if debug:
            print(f"  Rule {i} ({path_join_rule.__class__.__name__}): {path_join_rule}")
            print(f"    Result: {new_result}")
        result = new_result

    final_result = "".join(result)
    if debug:
        print(f"Final result: {final_result}\n")

    return final_result


# === config.py ===
def _parse_path_rule_from_dict(rule_dict: dict) -> PathRule:
    """Convert a dict from YAML into a PathRule dataclass."""
    rule_type = rule_dict.pop("type")

    if rule_type == "split":
        return SplitPathRule.from_dict(rule_dict)
    elif rule_type == "delete":
        return DeletePathRule.from_dict(rule_dict)
    else:
        raise ValueError(f'unknown path_rule type {rule_type}')


def _parse_path_join_rule_from_dict(rule_dict: dict) -> PathJoinRule:
    """Convert a dict from YAML into a PathJoinRule dataclass."""
    rule_type = rule_dict.pop("type")

    if rule_type == "replace":
        return ReplacePathJoinRule.from_dict(rule_dict)
    elif rule_type == "delete":
        return DeletePathJoinRule.from_dict(rule_dict)
    else:
        raise ValueError(f'unknown path_join_rule type {rule_type}')


def load_config(config_file: str) -> Config:
    """Load configuration from YAML file and merge with defaults."""
    user_config = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                user_config = loaded

    # Start with default config as dict
    config_dict = {
        "repo_root": DEFAULT_CONFIG.repo_root,
        "clone": {"default_depth": DEFAULT_CONFIG.clone.default_depth},
        "path_rules": [],
        "path_join_rules": [],
        "include_default_path_rules": DEFAULT_CONFIG.include_default_path_rules,
        "hub_cmd": DEFAULT_CONFIG.hub_cmd,
    }

    # Merge user config
    config_dict = deep_merge_dicts(config_dict, user_config)

    # Parse path rules from dicts to dataclasses
    path_rules: PathRules = []
    if config_dict["include_default_path_rules"]:
        path_rules.extend(DEFAULT_PATH_RULES)

    for rule_dict in config_dict.get("path_rules", []):
        path_rules.append(_parse_path_rule_from_dict(rule_dict))

    # Parse path join rules
    path_join_rules: PathJoinRules = []
    for rule_dict in config_dict.get("path_join_rules", []):
        path_join_rules.append(_parse_path_join_rule_from_dict(rule_dict))

    # Create Config object
    return Config(
        repo_root=config_dict["repo_root"],
        clone=CloneConfig(default_depth=config_dict["clone"]["default_depth"]),
        path_rules=path_rules,
        path_join_rules=path_join_rules,
        include_default_path_rules=config_dict["include_default_path_rules"],
        hub_cmd=config_dict.get("hub_cmd", "hub"),
    )


# === main.py ===
app = typer.Typer()


@app.command()
def clone(
    repo: str,
    depth: Optional[int] = typer.Option(None, help="Clone depth (use -1 for unlimited)"),
    auto_pull: bool = typer.Option(
        False,
        help="If specified and the local repo already exists, pull the latest commits from the default origin instead",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show the git commands that would be run without executing them",
    ),
    config_file: str = typer.Option(
        os.path.expanduser("~/.config/grm/grm.yaml"),
        "--config",
        help="Path to configuration file",
    ),
) -> None:
    """Clone a repository using grm path rules."""
    config = load_config(config_file)

    target_directory = process_path_rules(config.path_rules, repo, debug=dry_run)
    target_directory = os.path.join(config.repo_root, *target_directory)

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

        cmd = ["git", "-C", target_directory, "pull", "--ff-only"]
        if dry_run:
            print(shlex.join(cmd))
        else:
            subprocess.run(cmd)

    else:
        cmd = [
            "git",
            "clone",
            "--recurse-submodules",
            repo,
            target_directory,
        ]

        if depth is not None:
            if depth != -1:
                cmd.append(f"--depth={depth}")
        elif config.clone.default_depth != -1:
            cmd.append(f"--depth={config.clone.default_depth}")

        if dry_run:
            print(shlex.join(cmd))
        else:
            subprocess.run(cmd)


@app.command()
def create(
    repo: str,
    private: bool = typer.Option(..., "--private/--no-private", "-p/-P", help="Create a private or public repository"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show the git commands that would be run without executing them",
    ),
    config_file: str = typer.Option(
        os.path.expanduser("~/.config/grm/grm.yaml"),
        "--config",
        help="Path to configuration file",
    ),
) -> None:
    """Create a new repository on GitHub."""
    config = load_config(config_file)
    repo_root = config.repo_root
    hub_cmd = os.path.expandvars(
        os.path.expanduser(config.hub_cmd.strip())
    )

    target_directory = process_path_join_rules(
        config.path_join_rules, os.path.abspath(repo), debug=dry_run
    )

    if not target_directory.startswith(repo_root):
        print(
            f"must be in repo_root ({repo_root.replace(os.environ['HOME'], '~')}) to use this command",
            file=sys.stderr,
        )
        sys.exit(1)

    if not dry_run and not (os.path.exists(hub_cmd) or shutil.which(hub_cmd)):
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

    if dry_run:
        print(shlex.join(cmd))
    else:
        subprocess.run(shlex.join(cmd), shell=True)


@app.command()
def update() -> None:
    """Update repositories (not yet implemented)."""
    raise NotImplementedError()


@app.command()
def show_config(
    config_file: str = typer.Option(
        os.path.expanduser("~/.config/grm/grm.yaml"),
        "--config",
        help="Path to configuration file",
    ),
) -> None:
    """Display the loaded configuration."""
    config = load_config(config_file)
    print(config)


if __name__ == "__main__":
    app()

# vim: ft=python
