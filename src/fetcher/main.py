from findmy.reports import (
    AppleAccount,
    LoginState,
    SmsSecondFactorMethod,
    TrustedDeviceSecondFactorMethod,
)
from findmy.reports.anisette import LocalAnisetteProvider
from findmy import FindMyAccessory
import datetime

store_path = "account.json"


def _login_sync(account: AppleAccount) -> None:
    email = input("email?  > ")
    password = input("passwd? > ")

    state = account.login(email, password)

    if state == LoginState.REQUIRE_2FA:  # Account requires 2FA
        # This only supports SMS methods for now
        methods = account.get_2fa_methods()

        # Print the (masked) phone numbers
        for i, method in enumerate(methods):
            if isinstance(method, TrustedDeviceSecondFactorMethod):
                print(f"{i} - Trusted Device")
            elif isinstance(method, SmsSecondFactorMethod):
                print(f"{i} - SMS ({method.phone_number})")

        ind = int(input("Method? > "))

        method = methods[ind]
        method.request()
        code = input("Code? > ")

        # This automatically finishes the post-2FA login flow
        method.submit(code)


try:
    acc = AppleAccount.from_json(store_path)
except FileNotFoundError:
    acc = AppleAccount(LocalAnisetteProvider())
    _login_sync(acc)
    acc.to_json(store_path)

airtag = FindMyAccessory(
    master_key=b"",
    skn=b"",
    sks=b"",
    paired_at=datetime.datetime(2023, 9, 13, 16, 34, 29, tzinfo=datetime.timezone.utc),
    name=None,
    model="",
    identifier="",
)

reports = acc.fetch_last_reports(airtag)
for report in sorted(reports):
    print(f" - {report}")
