"""Tests for the notification rate-limiting logic. The real osascript call
was verified manually (see CHANGELOG) — tests mock subprocess.run so an
automated test run doesn't pop up real macOS notifications."""

from unittest.mock import MagicMock, patch

from macmine_lab import notifications


def _ok_result():
    result = MagicMock()
    result.returncode = 0
    return result


def test_send_calls_osascript_with_message_and_title():
    notifications._last_sent.clear()
    with patch("subprocess.run", return_value=_ok_result()) as mock_run:
        sent = notifications.send("MacMine Lab", "Hello", "unique_kind_1")
    assert sent is True
    args = mock_run.call_args[0][0]
    assert args[0] == "osascript"
    assert "Hello" in args[2]
    assert "MacMine Lab" in args[2]


def test_send_rate_limits_same_kind():
    notifications._last_sent.clear()
    with patch("subprocess.run", return_value=_ok_result()) as mock_run:
        first = notifications.send("T", "M1", "unique_kind_2")
        second = notifications.send("T", "M2", "unique_kind_2")
    assert first is True
    assert second is False
    assert mock_run.call_count == 1


def test_send_does_not_rate_limit_different_kinds():
    notifications._last_sent.clear()
    with patch("subprocess.run", return_value=_ok_result()):
        first = notifications.send("T", "M1", "kind_a")
        second = notifications.send("T", "M2", "kind_b")
    assert first is True
    assert second is True


def test_send_returns_false_on_nonzero_exit_without_raising():
    notifications._last_sent.clear()
    failure = MagicMock()
    failure.returncode = 1
    with patch("subprocess.run", return_value=failure):
        sent = notifications.send("T", "M", "unique_kind_3")
    assert sent is False


def test_send_returns_false_on_subprocess_error_without_raising():
    notifications._last_sent.clear()
    with patch("subprocess.run", side_effect=OSError("no osascript")):
        sent = notifications.send("T", "M", "unique_kind_4")
    assert sent is False


def test_osa_string_escapes_quotes_and_backslashes():
    assert notifications._osa_string('say "hi"') == '"say \\"hi\\""'
    assert notifications._osa_string("back\\slash") == '"back\\\\slash"'
