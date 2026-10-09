"""Conservative exposure guard; this is not a general image-quality classifier."""

from io import BytesIO
import warnings

from PIL import Image, ImageStat, UnidentifiedImageError


def is_extremely_dark(photo: bytes) -> bool:
    """Reject near-black frames, not ordinary shadows or dark backgrounds."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(photo)) as source:
                source.thumbnail((256, 256))
                gray = source.convert('L')
                histogram = gray.histogram()
                pixels = gray.width * gray.height
                return ImageStat.Stat(gray).mean[0] < 12 and sum(histogram[:32]) / pixels > .95
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        # Format validation / provider errors use the existing fail-closed path.
        return False
