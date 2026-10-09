"""Re-authenticating the stored Apple session.

Apple expires the session every so often. When that happens findmy tries to log
in again by itself, Apple asks for a second factor, and findmy gives up:

    Unexpected login state after reauth: LoginState.REQUIRE_2FA. Please log in again.

which kills the fetcher until somebody produces a fresh session. These helpers
let the admin do it: the stored account already holds the username and password,
so all that is missing is the code.

The login is two requests — ask for the code, then submit it — and the part-way
state rides between them as JSON, because findmy serialises the login state and
restores it in full. Nothing is kept in process memory, so it survives whichever
gunicorn worker answers.
"""

from findmy.reports import (
    AppleAccount,
    LoginState,
    SmsSecondFactorMethod,
    TrustedDeviceSecondFactorMethod,
)
from findmy.reports.anisette import LocalAnisetteProvider

# findmy wants somewhere to cache the anisette libraries it downloads
ANISETTE_LIBS_PATH = "/tmp/ani_libs.bin"  # noqa: S108

# A finished login lands on LOGGED_IN; AUTHENTICATED is the step before it,
# where the account is known to Apple but has not fetched its mobileme data
SIGNED_IN = (LoginState.LOGGED_IN, LoginState.AUTHENTICATED)


class ReauthError(Exception):
    """Something went wrong that the person in the admin needs to read."""


def _restore(state):
    try:
        return AppleAccount.from_json(state, anisette_libs_path=ANISETTE_LIBS_PATH)
    except (ValueError, KeyError, AssertionError) as error:
        raise ReauthError(f"Could not read the stored account: {error}") from error


def describe_method(method):
    """How the method should read in the dropdown."""
    if isinstance(method, TrustedDeviceSecondFactorMethod):
        return "Trusted device"
    if isinstance(method, SmsSecondFactorMethod):
        return f"SMS to {method.phone_number}"
    return type(method).__name__


def start_fresh(username, password):
    """Log in from nothing, for a project that has never had a session.

    Same handshake, but the account is built from scratch rather than restored,
    so Apple issues it a new device identity.
    """
    account = AppleAccount(LocalAnisetteProvider(libs_path=ANISETTE_LIBS_PATH))
    try:
        login_state = account.login(username, password)
    except Exception as error:
        raise ReauthError(f"Apple refused the login: {error}") from error

    return _offer_second_factors(account, login_state)


def _offer_second_factors(account, login_state):
    if login_state in SIGNED_IN:
        # Apple asked for nothing more, so the session is already good
        return account.to_json(), []

    if login_state != LoginState.REQUIRE_2FA:
        raise ReauthError(f"Apple answered with an unexpected state: {login_state}.")

    methods = account.get_2fa_methods()
    if not methods:
        raise ReauthError("Apple wants a second factor but offered no way to send one.")

    return account.to_json(), [
        (index, describe_method(method)) for index, method in enumerate(methods)
    ]


def request_code(state, index):
    """Ask Apple to send the code by the chosen method."""
    account = _restore(state)
    methods = account.get_2fa_methods()
    try:
        method = methods[index]
    except IndexError:
        raise ReauthError("That second factor is no longer on offer.") from None

    method.request()
    return account.to_json(), describe_method(method)


def submit_code(state, index, code):
    """Finish the login and hand back the account to store."""
    account = _restore(state)
    methods = account.get_2fa_methods()
    try:
        method = methods[index]
    except IndexError:
        raise ReauthError("That second factor is no longer on offer.") from None

    try:
        method.submit(code)
    except Exception as error:  # findmy raises its own errors for a bad code
        raise ReauthError(f"Apple rejected that code: {error}") from error

    if account.login_state not in SIGNED_IN:
        raise ReauthError(f"Still not logged in after the code: {account.login_state}.")

    return account.to_json()
