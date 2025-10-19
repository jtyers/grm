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
from grm import ReplacePathJoinRule, DeletePathJoinRule


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


if __name__ == '__main__':
    import pytest
    import sys
    # Run pytest on this file's directory to discover tests
    sys.exit(pytest.main(['-v', '-s']))
