import urllib.request
from urllib.parse import urlsplit

from akari_kopa.use_cases.listing.ports import ServiceError

SAFE_SCHEME = "https"


class RedirectRefused(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, answer, code, message, headers, new_address):
        raise ServiceError(f"{urlsplit(request.full_url).netloc} sent the request elsewhere ({code}); it was not followed")


def without_redirects() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(RedirectRefused)


class Destinations:
    def __init__(self, hosts: frozenset[str]):
        self.hosts = hosts

    def check(self, address: str) -> None:
        parts = urlsplit(address)
        if not self._allowed(parts):
            raise ServiceError(f"refused to send the login to {parts.netloc}: only https to {', '.join(sorted(self.hosts))}")

    def _allowed(self, parts) -> bool:
        if parts.scheme != SAFE_SCHEME or parts.port is not None:
            return False
        if parts.username is not None or parts.password is not None:
            return False
        return parts.netloc in self.hosts
