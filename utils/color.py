from colorthief import ColorThief


def get_dominant_color(path, quality=1):
    color_thief = ColorThief(path)
    (r, g, b) = color_thief.get_color(quality=quality)
    return '#{0:02x}{1:02x}{2:02x}'.format(r, g, b)
