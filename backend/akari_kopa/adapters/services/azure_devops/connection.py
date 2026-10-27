from akari_kopa.adapters.services.azure_devops.places import HOSTS
from akari_kopa.adapters.transport.https import Https
from akari_kopa.adapters.transport.https_guard import Destinations, without_redirects


def azure_connection(token: str) -> Https:
    return Https(token, Destinations(HOSTS), without_redirects())
