import pytest

FETCHER_TOKEN = "test-fetcher-token"


@pytest.fixture
def fetcher_headers(settings):
    """What the fetcher sends: its shared token, no Django user behind it."""
    settings.FETCHER_TOKEN = FETCHER_TOKEN
    return {"HTTP_AUTHORIZATION": f"Bearer {FETCHER_TOKEN}"}
