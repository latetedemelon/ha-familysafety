"""Constants for the Microsoft Family Safety integration."""
from logging import Logger, getLogger
from pyfamilysafety.account import OverrideTarget

LOGGER: Logger = getLogger(__package__)

NAME = "Microsoft Family Safety"
DOMAIN = "family_safety"

CONF_KEY_EXPR = "experimental"
CONF_EXPR_DEFAULT = False

DEFAULT_OVERRIDE_ENTITIES = [
    OverrideTarget.WINDOWS,
    OverrideTarget.XBOX
]
AGG_ERROR = ("Aggregator error occured. "
             "This is an upstream issue with Microsoft and is usually temporary. "
             "Try reloading the integration in 15 minutes.")

DOCS_URL = "https://github.com/pantherale0/ha-familysafety"
MS_LOGIN_URL = (
    "https://login.live.com/oauth20_authorize.srf"
    "?cobrandid=b5d15d4b-695a-4cd5-93c6-13f551b310df"
    "&client_id=000000000004893A"
    "&response_type=code"
    "&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf"
    "&response_mode=query"
    "&scope=service%3A%3Afamilymobile.microsoft.com%3A%3AMBI_SSL"
    "&lw=1&fl=easi2&login_hint="
)
