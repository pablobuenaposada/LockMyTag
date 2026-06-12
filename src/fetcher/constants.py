import os

_url_domain = os.environ.get("API_URL")

SLEEP_SECONDS = int(os.environ.get("SLEEP_SECONDS"))
TAGS_REFRESH_SECONDS = int(os.environ.get("TAGS_REFRESH_SECONDS"))
TAGS_ENDPOINT = f"{_url_domain}/api/tags/"
LOCATIONS_ENDPOINT = f"{_url_domain}/api/locations/"
ACCOUNT_ENDPOINT = f"{_url_domain}/api/account/"
USERNAME = os.environ.get("API_USERNAME")
PASSWORD = os.environ.get("API_PASSWORD")
BATTERY_FULL = "full"
BATTERY_MEDIUM = "medium"
BATTERY_LOW = "low"
BATTERY_VERY_LOW = "very_low"
BATTERY_LEVEL = {
    0b00: BATTERY_FULL,
    0b01: BATTERY_MEDIUM,
    0b10: BATTERY_LOW,
    0b11: BATTERY_VERY_LOW,
}
