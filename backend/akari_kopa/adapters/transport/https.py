import base64
import json
import urllib.error
import urllib.parse
import urllib.request

from akari_kopa.use_cases.listing.ports import ServiceError

TIMEOUT_SECONDS = 30


class Https:
    def __init__(self, base: str, authorization: str):
        self.base = base
        self.authorization = authorization

    @classmethod
    def basic(cls, base: str, credentials: str) -> "Https":
        return cls(base, "Basic " + base64.b64encode(credentials.encode()).decode())

    @classmethod
    def bearer(cls, base: str, token: str) -> "Https":
        return cls(base, "Bearer " + token)

    def get(self, path: str, **parameters: str):
        return self._fetch(self.base + path + _query(parameters))

    def post(self, path: str, body: dict, **parameters: str):
        return self._fetch(self.base + path + _query(parameters), json.dumps(body).encode())

    def pages(self, path: str, **parameters: str) -> list:
        page = self.get(path, **parameters)
        values = list(page["values"])
        while page.get("next"):
            page = self._fetch(page["next"])
            values += page["values"]
        return values

    def _fetch(self, url: str, body: bytes | None = None):
        headers = {"Authorization": self.authorization, "Accept": "application/json", "Content-Type": "application/json"}
        request = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as answer:
                return _data(answer, url)
        except urllib.error.HTTPError as error:
            raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} refused the request: {error.code} {error.reason}") from error
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} could not be read: {error}") from error


def _data(answer, url: str):
    if answer.headers.get_content_type() != "application/json":
        raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} answered with a web page, not data: the login or key may be wrong or expired")
    return json.load(answer)


def _query(parameters: dict[str, str]) -> str:
    return "?" + urllib.parse.urlencode(parameters) if parameters else ""
