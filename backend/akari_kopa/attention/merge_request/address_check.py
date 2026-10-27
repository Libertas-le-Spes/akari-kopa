from urllib.parse import urlsplit

from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress

SAFE_SCHEME = "https"


class UnsafeAddress(ValueError):
    pass


def address_of(text: str, forge_host: str) -> WebAddress | RefusedAddress:
    try:
        return checked(text, forge_host)
    except UnsafeAddress as refusal:
        return RefusedAddress(str(refusal), forge_host)


def checked(text: str, forge_host: str) -> WebAddress:
    _refuse_nothing(text)
    _refuse_hidden_characters(text)
    parts = urlsplit(text)
    _refuse_other_schemes(parts.scheme)
    _refuse_logins(parts)
    _refuse_other_hosts(parts.netloc, forge_host)
    return WebAddress(text, forge_host)


def _refuse_nothing(text: str) -> None:
    if not text:
        raise UnsafeAddress("the forge gave no address that can be opened")


def _refuse_hidden_characters(text: str) -> None:
    for character in text:
        if _hides_something(character):
            raise UnsafeAddress("the address holds a space, a backslash or a hidden character")


def _hides_something(character: str) -> bool:
    if character == "\\":
        return True
    return character.isspace() or not character.isprintable()


def _refuse_other_schemes(scheme: str) -> None:
    if scheme != SAFE_SCHEME:
        raise UnsafeAddress("only https addresses are opened")


def _refuse_logins(parts) -> None:
    if parts.username is not None or parts.password is not None:
        raise UnsafeAddress("the address carries a user name or password")


def _refuse_other_hosts(netloc: str, forge_host: str) -> None:
    if netloc.lower() != forge_host.lower():
        raise UnsafeAddress(f"the address does not point to {forge_host}")
