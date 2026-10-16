from merge_requests.presenters.orb.look import Look
from merge_requests.use_cases.desktop.ports import Pixmap

SIZES = (16, 22, 24, 32, 48, 64)
SAMPLES = 4
FADED_OPACITY = 0.45


def pixmaps(look: Look) -> list[Pixmap]:
    return [_pixmap(size, look) for size in SIZES]


def _rgb(colour: str) -> bytes:
    return bytes.fromhex(colour.lstrip("#"))


def _pixmap(size: int, look: Look) -> Pixmap:
    radius = size * 0.34
    ring = max(1.0, size * 0.09) if look.ring else None
    opacity = FADED_OPACITY if look.faded else 1.0
    rgb = _rgb(look.colour)
    pixels = (bytes([round(255 * opacity * _coverage(x, y, size, radius, ring))]) + rgb for y in range(size) for x in range(size))
    return Pixmap(size, size, b"".join(pixels))


def _coverage(x: int, y: int, size: int, radius: float, ring: float | None) -> float:
    centre = size / 2
    inside = 0
    for sx in range(SAMPLES):
        for sy in range(SAMPLES):
            distance = ((x + (sx + 0.5) / SAMPLES - centre) ** 2 + (y + (sy + 0.5) / SAMPLES - centre) ** 2) ** 0.5
            inside += _covered(distance, radius, ring)
    return inside / (SAMPLES * SAMPLES)


def _covered(distance: float, radius: float, ring: float | None) -> bool:
    return distance <= radius and (ring is None or distance >= radius - ring)
