from unittest.mock import MagicMock, patch

import pytest
from findmy.reports import LoginState

from account.apple import ReauthError, start_fresh


def _account(login_state=LoginState.REQUIRE_2FA, methods=(MagicMock(),)):
    account = MagicMock()
    account.login.return_value = login_state
    account.get_2fa_methods.return_value = list(methods)
    account.to_json.return_value = {"type": "account"}
    return account


class TestsStartFresh:
    def test_logs_in_with_what_was_typed(self):
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            apple.return_value = _account()
            start_fresh("pablo@example.com", "hunter2")

        apple.return_value.login.assert_called_once_with("pablo@example.com", "hunter2")

    def test_offers_the_second_factors(self):
        first, second = MagicMock(), MagicMock()
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            apple.return_value = _account(methods=(first, second))
            _, methods = start_fresh("pablo@example.com", "hunter2")

        assert [index for index, _ in methods] == [0, 1]

    def test_apple_asking_for_nothing_more(self):
        """A finished login lands on LOGGED_IN, not AUTHENTICATED."""
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            account = _account(login_state=LoginState.LOGGED_IN)
            account.to_json.return_value = {"renewed": True}
            apple.return_value = account
            state, methods = start_fresh("pablo@example.com", "hunter2")

        assert methods == []
        assert state == {"renewed": True}

    def test_an_unexpected_state(self):
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            apple.return_value = _account(login_state=LoginState.LOGGED_OUT)

            with pytest.raises(ReauthError, match="unexpected state"):
                start_fresh("pablo@example.com", "hunter2")

    def test_two_factor_but_no_methods(self):
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            apple.return_value = _account(methods=())

            with pytest.raises(ReauthError, match="no way to send"):
                start_fresh("pablo@example.com", "hunter2")

    def test_apple_refusing_the_login(self):
        with (
            patch("account.apple.AppleAccount") as apple,
            patch("account.apple.LocalAnisetteProvider"),
        ):
            apple.return_value.login.side_effect = RuntimeError("bad password")

            with pytest.raises(ReauthError, match="Apple refused the login"):
                start_fresh("pablo@example.com", "wrong")
