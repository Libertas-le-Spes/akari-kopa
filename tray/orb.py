SIZES = (16, 22, 24, 32, 48, 64)

COLOURS = {
    ("mine", "passing"): (0x3F, 0xB9, 0x50),
    ("mine", "failing"): (0xF8, 0x51, 0x49),
    ("review", "passing"): (0x4C, 0x8D, 0xFF),
    ("review", "failing"): (0xE3, 0xB3, 0x41),
}

UNKNOWN = (0x9A, 0xA0, 0xA6)
SAMPLES = 4


def colour_for(role, pipeline):
    return COLOURS.get((role, "failing" if pipeline == "failing" else "passing"), UNKNOWN)


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


def orb(role, pipeline, faded=False):
    colour = colour_for(role, pipeline)
    hollow = pipeline not in ("passing", "failing")
    return [pixmap(size, colour, hollow, faded) for size in SIZES]
