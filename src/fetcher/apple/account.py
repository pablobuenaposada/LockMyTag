from findmy.reports import (
    AppleAccount,
    LoginState,
    SmsSecondFactorMethod,
    TrustedDeviceSecondFactorMethod,
)
from findmy.reports.anisette import LocalAnisetteProvider

STORE_PATH = "account.json"
ANI_LIB_PATH = "ani_libs.bin"


def login(account_json):
    try:
        account = AppleAccount.from_json(account_json, anisette_libs_path=ANI_LIB_PATH)
    except FileNotFoundError:
        account = AppleAccount(LocalAnisetteProvider())
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

        account.to_json(
            STORE_PATH
        )  # login worked so let's store the account for next time

    return account
