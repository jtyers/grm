#!/usr/bin/env -S uv run --with pytest --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["typer", "pyyaml"]
# ///
"""
Test suite for grm path join rules
"""

import re
from dataclasses import dataclass
from typer.testing import CliRunner
from grm import ReplacePathJoinRule, DeletePathJoinRule, app


runner = CliRunner()


def test_replace_path_join_rule_basic():
    """Test basic ReplacePathJoinRule functionality."""
    rule = ReplacePathJoinRule(exact_match='/foo/', replace='-foo-')
    result = rule.process(['/home/user/foo/bar'])
    assert result == ['/home/user-foo-bar']


def test_replace_path_join_rule_multiple():
    """Test ReplacePathJoinRule with multiple items."""
    rule = ReplacePathJoinRule(exact_match='/tf-modules/', replace='-tf-modules-')
    result = rule.process(['/home/user/tf-modules/repo', '/another/tf-modules/path'])
    assert result == ['/home/user-tf-modules-repo', '/another-tf-modules-path']


def test_replace_path_join_rule_no_match():
    """Test ReplacePathJoinRule when there's no match."""
    rule = ReplacePathJoinRule(exact_match='/nonexistent/', replace='-foo-')
    result = rule.process(['/home/user/bar'])
    assert result == ['/home/user/bar']


def test_delete_path_join_rule_basic():
    """Test basic DeletePathJoinRule functionality."""
    rule = DeletePathJoinRule(regex=r'/git/')
    result = rule.process(['/home/jonny/git/repo'])
    # Regex removes '/git/' including the slashes, leaving '/home/jonnyrepo'
    assert result == ['/home/jonnyrepo']


def test_delete_path_join_rule_protocol():
    """Test DeletePathJoinRule removing protocol."""
    rule = DeletePathJoinRule(regex=r'^https?://')
    result = rule.process(['https://github.com/user/repo', 'http://example.com'])
    assert result == ['github.com/user/repo', 'example.com']


def test_delete_path_join_rule_no_match():
    """Test DeletePathJoinRule when there's no match."""
    rule = DeletePathJoinRule(regex=r'nonexistent')
    result = rule.process(['/home/user/repo'])
    assert result == ['/home/user/repo']


def test_delete_path_join_rule_multiple_matches():
    """Test DeletePathJoinRule with multiple matches in same string."""
    rule = DeletePathJoinRule(regex=r'test')
    result = rule.process(['testfoo-test-bar'])
    assert result == ['foo--bar']


def test_replace_path_join_rule_regex_basic():
    """Test ReplacePathJoinRule with regex mode."""
    rule = ReplacePathJoinRule(regex=r'/git/', replace='/code/')
    result = rule.process(['/home/user/git/repo'])
    assert result == ['/home/user/code/repo']


def test_replace_path_join_rule_regex_pattern():
    """Test ReplacePathJoinRule with regex pattern."""
    rule = ReplacePathJoinRule(regex=r'(internal|external)', replace='common')
    result = rule.process(['/home/internal/repo', '/home/external/repo'])
    assert result == ['/home/common/repo', '/home/common/repo']


def test_replace_path_join_rule_regex_capture_groups():
    """Test ReplacePathJoinRule with regex capture groups."""
    rule = ReplacePathJoinRule(regex=r'/(\w+)-modules/', replace=r'/\1/')
    result = rule.process(['/home/tf-modules/repo', '/home/py-modules/code'])
    assert result == ['/home/tf/repo', '/home/py/code']


def test_replace_path_join_rule_validation_both():
    """Test that specifying both exact_match and regex raises error."""
    try:
        ReplacePathJoinRule(exact_match='/foo/', regex=r'/bar/', replace='test')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "only one of 'exact_match' or 'regex'" in str(e)


def test_replace_path_join_rule_validation_neither():
    """Test that specifying neither exact_match nor regex raises error."""
    try:
        ReplacePathJoinRule(replace='test')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "one of 'exact_match' or 'regex' must be specified" in str(e)


def test_combined_rules():
    """Test combining both rule types."""
    rules = [
        DeletePathJoinRule(regex=r'^/home/jonny/git/'),
        ReplacePathJoinRule(exact_match='/internal/', replace='-internal-')
    ]

    path = ['/home/jonny/git/internal/repo']
    for rule in rules:
        path = rule.process(path)

    # After delete: 'internal/repo', after replace: 'internal/repo' (no match for '/internal/')
    assert path == ['internal/repo']


def test_clone_errors_when_target_exists_without_ignore_existing(tmp_path):
    """Existing clone targets are still errors by default."""
    repo_root = tmp_path / "git"
    target = repo_root / "owner" / "repo"
    target.mkdir(parents=True)
    config_file = tmp_path / "grm.yaml"
    config_file.write_text(f"repo_root: {repo_root}\n")

    result = runner.invoke(
        app,
        ["clone", "https://example.com/owner/repo.git", "--config", str(config_file)],
    )

    assert result.exit_code != 0
    assert "already exists" in result.output


def test_clone_ignore_existing_returns_success_for_existing_target(tmp_path):
    """--ignore-existing skips existing targets without validating their remote."""
    repo_root = tmp_path / "git"
    target = repo_root / "owner" / "repo"
    target.mkdir(parents=True)
    config_file = tmp_path / "grm.yaml"
    config_file.write_text(f"repo_root: {repo_root}\n")

    result = runner.invoke(
        app,
        [
            "clone",
            "https://example.com/owner/repo.git",
            "--ignore-existing",
            "--auto-pull",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""


if __name__ == '__main__':
    import pytest
    import sys
    # Run pytest on this file's directory to discover tests
    sys.exit(pytest.main(['-v', '-s']))
