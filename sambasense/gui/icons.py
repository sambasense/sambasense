"""Programmatic SVG icon builder for SambaSense.

Generates QIcon objects from inline SVG strings so no external icon files are needed.
All icons use the current accent color for consistency with the theme.
"""

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray


def _render_svg(svg: str, size: int = 24) -> QPixmap:
    """Render an SVG string to a QPixmap."""
    data = QByteArray(svg.encode("utf-8"))
    renderer = QSvgRenderer(data)
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def _icon_from_svg(svg: str, size: int = 24) -> QIcon:
    """Create a QIcon from an SVG string."""
    return QIcon(_render_svg(svg, size))


def icon_folder(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M2 6a2 2 0 012-2h5l2 2h9a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
            fill="{color}" fill-opacity="0.2" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_folder_share(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M2 6a2 2 0 012-2h5l2 2h9a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
            fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="15" cy="9" r="1.5" fill="{color}"/>
      <circle cx="10" cy="14" r="1.5" fill="{color}"/>
      <circle cx="17" cy="15" r="1.5" fill="{color}"/>
      <line x1="14" y1="10" x2="11" y2="13" stroke="{color}" stroke-width="1"/>
      <line x1="16" y1="14" x2="12" y2="14.5" stroke="{color}" stroke-width="1"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_server(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <rect x="3" y="3" width="18" height="7" rx="2" fill="{color}" fill-opacity="0.15"
            stroke="{color}" stroke-width="1.5"/>
      <rect x="3" y="14" width="18" height="7" rx="2" fill="{color}" fill-opacity="0.15"
            stroke="{color}" stroke-width="1.5"/>
      <circle cx="7" cy="6.5" r="1" fill="{color}"/>
      <circle cx="7" cy="17.5" r="1" fill="{color}"/>
      <line x1="11" y1="6.5" x2="17" y2="6.5" stroke="{color}" stroke-width="1" stroke-linecap="round"/>
      <line x1="11" y1="17.5" x2="17" y2="17.5" stroke="{color}" stroke-width="1" stroke-linecap="round"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_download(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M12 3v12m0 0l-4-4m4 4l4-4" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" stroke="{color}" stroke-width="1.8" stroke-linecap="round" fill="none"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_link(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"
            stroke="{color}" stroke-width="1.8" stroke-linecap="round" fill="none"/>
      <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"
            stroke="{color}" stroke-width="1.8" stroke-linecap="round" fill="none"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_chart_pie(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M21.21 15.89A10 10 0 118.11 2.79" stroke="{color}" stroke-width="1.8" fill="none"/>
      <path d="M22 12A10 10 0 0012 2v10z" fill="{color}" fill-opacity="0.3" stroke="{color}" stroke-width="1.5"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_chart_line(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <polyline points="4,18 8,12 12,14 16,8 20,10" stroke="{color}" stroke-width="1.8" stroke-linecap="round"
                stroke-linejoin="round" fill="none"/>
      <line x1="3" y1="20" x2="21" y2="20" stroke="{color}" stroke-opacity="0.3" stroke-width="1"/>
      <line x1="3" y1="4" x2="3" y2="20" stroke="{color}" stroke-opacity="0.3" stroke-width="1"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_settings(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="1.5" fill="none"/>
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33
              1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1.08-1.51 1.65 1.65 0 00-1.82.33l-.06.06
              a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09
              a1.65 1.65 0 001.51-1.08 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06
              a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001.08 1.51
              1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9
              a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1.08z"
            stroke="{color}" stroke-width="1.3" fill="none"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_sun(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <circle cx="12" cy="12" r="5" stroke="{color}" stroke-width="1.5" fill="{color}" fill-opacity="0.2"/>
      <line x1="12" y1="1" x2="12" y2="3" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="12" y1="21" x2="12" y2="23" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="1" y1="12" x2="3" y2="12" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="21" y1="12" x2="23" y2="12" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_moon(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
            stroke="{color}" stroke-width="1.5" fill="{color}" fill-opacity="0.2"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_palette(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01
              -.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-4.96-4.49-9-10-9z"
            fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="1.5"/>
      <circle cx="8" cy="10" r="1.5" fill="#ef4444"/>
      <circle cx="12" cy="7" r="1.5" fill="#3b82f6"/>
      <circle cx="16" cy="10" r="1.5" fill="#22c55e"/>
      <circle cx="9" cy="14" r="1.5" fill="#a855f7"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_home(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1m-2 0h2"
            stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_trash(color: str = "#ff4d6a", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"
            stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <line x1="10" y1="11" x2="10" y2="17" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="14" y1="11" x2="14" y2="17" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_plus(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <line x1="12" y1="5" x2="12" y2="19" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
      <line x1="5" y1="12" x2="19" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
    </svg>'''
    return _icon_from_svg(svg, size)


def icon_refresh(color: str = "#FFD700", size: int = 24) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
      <path d="M23 4v6h-6M1 20v-6h6" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"
            stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>'''
    return _icon_from_svg(svg, size)
