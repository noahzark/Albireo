from colorthief import ColorThief


def get_dominant_color(path, quality=1):
    """
    This method get the dominant color for an image.
    may throw exception.
    :param path: image path
    :param quality: resample quality 1 ~ 10 the higher the fast but not accurate, 
    :return: a hex string like #ff0f0f
    """
    color_thief = ColorThief(path)
    (r, g, b) = color_thief.get_color(quality=quality)
    return '#{0:02x}{1:02x}{2:02x}'.format(r, g, b)
