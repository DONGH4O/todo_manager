"""Generate Todo Manager application icon assets.

The source motif mirrors the Figma-derived brand lockup used by the runtime UI:
a rounded gradient brand mark plus the white brand letter "T".
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen


ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "assets" / "icons"
BRAND_PRIMARY = QColor("#2e8df5")
BRAND_SECONDARY = QColor("#23b883")

PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
ICNS_CHUNKS = (
    ("icp4", 16),
    ("icp5", 32),
    ("icp6", 64),
    ("ic07", 128),
    ("ic08", 256),
    ("ic09", 512),
    ("ic10", 1024),
)


def _png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Qt failed to encode PNG data")
    return bytes(data)


def _rounded_rect(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def render_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    inset = size * 0.075
    rect = QRectF(inset, inset, size - inset * 2, size - inset * 2)
    radius = size * 0.22

    shadow = QColor("#123047")
    for step, alpha in enumerate((28, 18, 10), start=1):
        shadow_rect = rect.translated(0, size * 0.01 * step)
        shadow.setAlpha(alpha)
        painter.fillPath(_rounded_rect(shadow_rect, radius), shadow)

    gradient = QLinearGradient(QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.bottom()))
    gradient.setColorAt(0.0, BRAND_PRIMARY)
    gradient.setColorAt(1.0, BRAND_SECONDARY)

    mark_path = _rounded_rect(rect, radius)
    painter.fillPath(mark_path, gradient)

    painter.setPen(QPen(QColor(255, 255, 255, 58), max(1, int(size * 0.012))))
    painter.drawPath(mark_path)

    highlight = QLinearGradient(QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.center().y()))
    highlight.setColorAt(0.0, QColor(255, 255, 255, 58))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.fillPath(mark_path, highlight)

    letter_path = QPainterPath()
    letter_radius = max(1.0, size * 0.025)
    letter_path.addPath(
        _rounded_rect(
            QRectF(size * 0.285, size * 0.295, size * 0.43, size * 0.11),
            letter_radius,
        )
    )
    letter_path.addPath(
        _rounded_rect(
            QRectF(size * 0.445, size * 0.37, size * 0.11, size * 0.34),
            letter_radius,
        )
    )
    painter.fillPath(letter_path, QColor("#ffffff"))

    painter.end()
    return image


def write_svg() -> None:
    svg = """<svg width="1024" height="1024" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="tmBrandGradient" x1="96" y1="96" x2="928" y2="928" gradientUnits="userSpaceOnUse">
      <stop stop-color="#2E8DF5"/>
      <stop offset="1" stop-color="#23B883"/>
    </linearGradient>
    <linearGradient id="tmBrandHighlight" x1="96" y1="96" x2="928" y2="512" gradientUnits="userSpaceOnUse">
      <stop stop-color="white" stop-opacity="0.24"/>
      <stop offset="1" stop-color="white" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="76" y="88" width="872" height="872" rx="224" fill="#123047" fill-opacity="0.10"/>
  <rect x="76" y="76" width="872" height="872" rx="224" fill="url(#tmBrandGradient)"/>
  <rect x="76" y="76" width="872" height="872" rx="224" fill="url(#tmBrandHighlight)"/>
  <rect x="82" y="82" width="860" height="860" rx="218" stroke="white" stroke-opacity="0.23" stroke-width="12"/>
  <rect x="292" y="302" width="440" height="112" rx="26" fill="white"/>
  <rect x="456" y="379" width="112" height="348" rx="26" fill="white"/>
</svg>
"""
    (ICON_DIR / "todo-manager.svg").write_text(svg, encoding="utf-8")


def write_ico(pngs: dict[int, bytes]) -> None:
    entries: list[bytes] = []
    payloads: list[bytes] = []
    offset = 6 + (16 * len(ICO_SIZES))

    for size in ICO_SIZES:
        payload = pngs[size]
        width = 0 if size == 256 else size
        height = 0 if size == 256 else size
        entries.append(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        payloads.append(payload)
        offset += len(payload)

    header = struct.pack("<HHH", 0, 1, len(ICO_SIZES))
    (ICON_DIR / "todo-manager.ico").write_bytes(header + b"".join(entries) + b"".join(payloads))


def write_icns(pngs: dict[int, bytes]) -> None:
    chunks: list[bytes] = []
    for chunk_type, size in ICNS_CHUNKS:
        payload = pngs[size]
        chunks.append(chunk_type.encode("ascii") + struct.pack(">I", len(payload) + 8) + payload)

    body = b"".join(chunks)
    (ICON_DIR / "todo-manager.icns").write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    pngs: dict[int, bytes] = {}
    for size in PNG_SIZES:
        image = render_icon(size)
        pngs[size] = _png_bytes(image)
        if size == 1024:
            image.save(str(ICON_DIR / "todo-manager.png"), "PNG")

    write_svg()
    write_ico(pngs)
    write_icns(pngs)
    print(f"Generated application icons in {ICON_DIR}")
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
