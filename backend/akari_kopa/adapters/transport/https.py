import json
import urllib.error
import urllib.parse
import urllib.request

from akari_kopa.adapters.transport.https_guard import Destinations
from akari_kopa.use_cases.listing.ports import ServiceError

TIMEOUT_SECONDS = 30
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


class Https:
    def __init__(self, token: str, destinations: Destinations, opener: urllib.request.OpenerDirector):
        self.authorization = "Bearer " + token
        self.destinations = destinations
        self.opener = opener

    def get(self, address: str, **parameters: str):
        return self._fetch(address + _query(parameters), None)

    def post(self, address: str, body: dict, **parameters: str):
        return self._fetch(address + _query(parameters), json.dumps(body).encode())

    def _fetch(self, address: str, body: bytes | None):
        self.destinations.check(address)
        request = urllib.request.Request(address, data=body, headers=HEADERS)
        request.add_unredirected_header("Authorization", self.authorization)
        host = urllib.parse.urlsplit(address).netloc
        try:
            with self.opener.open(request, timeout=TIMEOUT_SECONDS) as answer:
                return _data(answer, host)
        except urllib.error.HTTPError as error:
            raise ServiceError(f"{host} refused the request: {error.code} {error.reason}") from error
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            raise ServiceError(f"{host} could not be read: {error}") from error


def _data(answer, host: str):
    if answer.headers.get_content_type() != "application/json":
        raise ServiceError(f"{host} answered with a web page, not data: the login may be wrong or expired")
    return json.load(answer)


def _query(parameters: dict[str, str]) -> str:
    if not parameters:
        return ""
    return "?" + urllib.parse.urlencode(parameters)
