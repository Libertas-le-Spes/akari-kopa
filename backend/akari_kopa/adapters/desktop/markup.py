import html

from akari_kopa.use_cases.desktop.ports import IconContent

APP_NAME = "Akari Kopa"
NOTICE_MILLISECONDS = 8000


def as_markup(text: str) -> str:
    return html.escape(text)


def tool_tip(content: IconContent) -> tuple:
    return "", [], as_markup(content.title), as_markup(content.description)


def notice(summary: str, body: str) -> tuple:
    return APP_NAME, 0, "", summary, as_markup(body), [], {}, NOTICE_MILLISECONDS
