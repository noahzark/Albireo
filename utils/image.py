from colorthief import ColorThief
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def get_dominant_color(path, quality=1):
    """
    This method get the dominant color for an image.
    may throw exception.
    :param path: image path
    :param quality: resample quality 1 ~ 10 the higher the fast but not accurate,
    :return: a hex string like #ff0f0f
    """
    try:
        color_thief = ColorThief(path)
        (r, g, b) = color_thief.get_color(quality=quality)
        return '#{0:02x}{1:02x}{2:02x}'.format(r, g, b)
    except Exception as error:
        logger.error(error, exc_info=True)
        return '#000000'


def get_dimension(path):
    try:
        im = Image.open(path)
        return im.size
    except Exception as error:
        logger.error(error, exc_info=True)
        return None, None
