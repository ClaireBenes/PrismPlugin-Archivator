from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap


def resolve_preview_path(image_path: str | None, placeholder_path: str | None) -> str | None:
    """
    Resolve the final preview image path.

    Priority:
    1. project image path if it exists
    2. placeholder path if it exists
    3. None
    """
    if image_path and Path(image_path).exists():
        return image_path

    if placeholder_path and Path(placeholder_path).exists():
        return placeholder_path

    return None


def load_pixmap(image_path: str | None) -> QPixmap | None:
    """
    Load a pixmap from disk.

    Returns:
        QPixmap | None: Loaded pixmap, or None if invalid.
    """
    if not image_path:
        return None

    pixmap = QPixmap(str(image_path))
    if pixmap.isNull():
        return None

    return pixmap


def build_rounded_pixmap(
    pixmap: QPixmap,
    width: int,
    height: int,
    radius: int,
    corners: str = "all",
) -> QPixmap:
    """
    Scale, crop, and round a pixmap.

    Args:
        pixmap (QPixmap): Source image.
        width (int): Output width.
        height (int): Output height.
        radius (int): Corner radius.
        corners (str): "all" or "top".

    Returns:
        QPixmap: Rendered rounded pixmap.
    """
    scaled = pixmap.scaled(
        width,
        height,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation,
    )

    result = QPixmap(width, height)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)

    path = QPainterPath()

    if corners == "top":
        w = width
        h = height
        r = radius

        path.moveTo(0, h)
        path.lineTo(0, r)
        path.quadTo(0, 0, r, 0)
        path.lineTo(w - r, 0)
        path.quadTo(w, 0, w, r)
        path.lineTo(w, h)
        path.closeSubpath()
    else:
        path.addRoundedRect(0, 0, width, height, radius, radius)

    painter.setClipPath(path)

    x = (scaled.width() - width) // 2
    y = (scaled.height() - height) // 2
    painter.drawPixmap(-x, -y, scaled)

    painter.end()

    return result


def build_preview_pixmap(
    image_path: str | None,
    placeholder_path: str | None,
    width: int,
    height: int,
    radius: int,
    corners: str = "all",
) -> QPixmap | None:
    """
    Resolve, load, scale, crop, and round a preview pixmap.

    Returns:
        QPixmap | None: Final pixmap, or None if no valid image exists.
    """
    final_path = resolve_preview_path(image_path, placeholder_path)
    pixmap = load_pixmap(final_path)

    if pixmap is None:
        return None

    return build_rounded_pixmap(
        pixmap=pixmap,
        width=width,
        height=height,
        radius=radius,
        corners=corners,
    )