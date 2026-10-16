import base64
import json
import urllib.error
import urllib.parse
import urllib.request

from merge_requests.use_cases.listing.ports import ServiceError

TIMEOUT_SECONDS = 30


class Https:
    def __init__(self, base: str, credentials: str):
        self.base = base
        self.authorization = "Basic " + base64.b64encode(credentials.encode()).decode()

    def get(self, path: str, **parameters: str):
        return self._fetch(self.base + path + _query(parameters))

    def pages(self, path: str, **parameters: str) -> list:
        page = self.get(path, **parameters)
        values = list(page["values"])
        while page.get("next"):
            page = self._fetch(page["next"])
            values += page["values"]
        return values

    def _fetch(self, url: str):
        request = urllib.request.Request(url, headers={"Authorization": self.authorization, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as answer:
                return json.load(answer)
        except urllib.error.HTTPError as error:
            raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} refused the request: {error.code} {error.reason}") from error
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} could not be read: {error}") from error


def _query(parameters: dict[str, str]) -> str:
    return "?" + urllib.parse.urlencode(parameters) if parameters else ""
