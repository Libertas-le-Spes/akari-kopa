SIZES = (16, 22, 24, 32, 48, 64)

GREEN = (0x3F, 0xB9, 0x50)
RED = (0xF8, 0x51, 0x49)
PURPLE = (0xA3, 0x71, 0xF7)
BLUE = (0x4C, 0x8D, 0xFF)
YELLOW = (0xE3, 0xB3, 0x41)

COLOURS = {
    "mine": {"passing": GREEN, "idle": GREEN, "pending": GREEN, "failing": RED, "comments": PURPLE},
    "review": {"passing": BLUE, "idle": BLUE, "pending": BLUE, "failing": YELLOW, "comments": BLUE},
}

UNKNOWN = (0x9A, 0xA0, 0xA6)
SAMPLES = 4


def colour_for(role, state):
    return COLOURS.get(role, {}).get(state, UNKNOWN)


def _coverage(x, y, size, radius, ring):
    centre = size / 2
    inside = 0
    for sx in range(SAMPLES):
        for sy in range(SAMPLES):
            px = x + (sx + 0.5) / SAMPLES - centre
            py = y + (sy + 0.5) / SAMPLES - centre
            distance = (px * px + py * py) ** 0.5
            if distance <= radius and (ring is None or distance >= radius - ring):
                inside += 1
    return inside / (SAMPLES * SAMPLES)


def pixmap(size, colour, hollow, faded):
    radius = size * 0.34
    ring = max(1.0, size * 0.09) if hollow else None
    opacity = 0.45 if faded else 1.0
    red, green, blue = colour
    data = bytearray()
    for y in range(size):
        for x in range(size):
            alpha = round(255 * opacity * _coverage(x, y, size, radius, ring))
            data += bytes((alpha, red, green, blue))
    return size, size, bytes(data)


def orb(role, state, faded=False):
    colour = colour_for(role, state)
    hollow = state == "pending"
    return [pixmap(size, colour, hollow, faded) for size in SIZES]
