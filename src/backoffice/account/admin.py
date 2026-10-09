from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .apple import ReauthError, request_code, start_fresh, submit_code
from .models import Account

# Where the part-way login lives between requests
SESSION_KEY = "apple_reauth"


class CredentialsForm(forms.Form):
    """Asked for on every login rather than read back out of the stored session."""

    username = forms.EmailField(label="Apple Account")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class MethodForm(forms.Form):
    method = forms.TypedChoiceField(
        coerce=int, label="Send the code by", widget=forms.RadioSelect
    )

    def __init__(self, *args, methods=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["method"].choices = methods


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Code from Apple",
        max_length=10,
        widget=forms.TextInput(
            attrs={"autocomplete": "one-time-code", "autofocus": ""}
        ),
    )


class AccountAdmin(admin.ModelAdmin):
    readonly_fields = ("created", "modified")
    change_list_template = "admin/account/account/change_list.html"

    def get_urls(self):
        return [
            path(
                "reauthenticate/",
                self.admin_site.admin_view(self.reauthenticate),
                name="account_account_reauthenticate",
            ),
            *super().get_urls(),
        ]

    def _render(self, request, **context):
        return render(
            request,
            "admin/account/account/reauthenticate.html",
            {
                **self.admin_site.each_context(request),
                "title": "Log in to Apple",
                "opts": self.model._meta,
                **context,
            },
        )

    def _store(self, account, state, request):
        """Keep the finished session, creating the account on a first login."""
        if account is None:
            Account.objects.create(data=state)
        else:
            account.data = state
            account.save()
        request.session.pop(SESSION_KEY, None)

    def reauthenticate(self, request):
        """Log the Apple account in, asking the operator for the second factor.

        Used both to set the project up and to recover afterwards: Apple expires
        the session every so often, and the fetcher cannot answer a second-factor
        prompt on its own, so it crash-loops until somebody does it here.
        """
        changelist = reverse("admin:account_account_changelist")
        account = Account.objects.first()
        pending = request.session.get(SESSION_KEY)

        # Last step: the code is in, finish the login and keep the session
        if request.method == "POST" and "code" in request.POST:
            if not pending:
                self.message_user(
                    request,
                    "That login timed out before the code arrived. Start again.",
                    messages.WARNING,
                )
                return redirect(request.path)

            form = CodeForm(request.POST)
            if form.is_valid():
                try:
                    state = submit_code(
                        pending["state"], pending["method"], form.cleaned_data["code"]
                    )
                except ReauthError as error:
                    self.message_user(request, str(error), messages.ERROR)
                else:
                    self._store(account, state, request)
                    self.message_user(request, "Apple session renewed.")
                    return redirect(changelist)

            return self._render(request, code_form=form, sent_by=pending["sent_by"])

        # Middle step: a second factor was chosen, ask Apple to send the code
        if request.method == "POST" and "method" in request.POST:
            if not pending:
                return redirect(request.path)

            form = MethodForm(request.POST, methods=pending["methods"])
            if form.is_valid():
                chosen = form.cleaned_data["method"]
                try:
                    state, sent_by = request_code(pending["state"], chosen)
                except ReauthError as error:
                    self.message_user(request, str(error), messages.ERROR)
                    return redirect(changelist)

                request.session[SESSION_KEY] = {
                    **pending,
                    "state": state,
                    "method": chosen,
                    "sent_by": sent_by,
                }
                return self._render(request, code_form=CodeForm(), sent_by=sent_by)

            return self._render(request, method_form=form)

        # First step: log in. Always asked for, so nothing has to lean on the
        # password findmy keeps inside the stored session.
        if request.method == "POST" and "password" in request.POST:
            credentials_form = CredentialsForm(request.POST)
            if not credentials_form.is_valid():
                return self._render(request, credentials_form=credentials_form)
            try:
                state, methods = start_fresh(
                    credentials_form.cleaned_data["username"],
                    credentials_form.cleaned_data["password"],
                )
            except ReauthError as error:
                self.message_user(request, str(error), messages.ERROR)
                return self._render(request, credentials_form=credentials_form)

        else:
            # Nothing typed yet, so ask. The username is prefilled from whatever
            # session is already stored, so only the password has to be retyped.
            stored = (account.data or {}).get("account") if account else None
            return self._render(
                request,
                credentials_form=CredentialsForm(
                    initial={"username": (stored or {}).get("username")}
                ),
            )

        if not methods:
            self._store(account, state, request)
            self.message_user(request, "Logged in to Apple.")
            return redirect(changelist)

        request.session[SESSION_KEY] = {"state": state, "methods": methods}
        return self._render(request, method_form=MethodForm(methods=methods))


admin.site.register(Account, AccountAdmin)
