from colorthief import ColorThief


def get_dominant_color(path):
    color_thief = ColorThief(path)
    (r, g, b) = color_thief.get_color(quality=1)
    return '#{0:02x}{1:02x}{2:02x}'.format(r, g, b)
