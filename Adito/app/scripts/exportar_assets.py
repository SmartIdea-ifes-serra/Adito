#!/usr/bin/env python3
"""Exporta e empacota a arte original do Adito, sem alterar sua paleta.

Dependências de desenvolvimento no Linux: python3-pil, python3-gi,
python3-cairo, python3-gi-cairo e gir1.2-rsvg-2.0. Não são dependências do app.
Os PNGs em public/brand/adito-{light,dark}.png são as fontes da marca.
Os SVGs incorporam esses PNGs sem perdas; não são uma vetorização da arte.
Os ícones Tauri existentes são preservados e incluídos no pacote.
"""

from __future__ import annotations

import ctypes
import base64
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import cairo
import gi
from PIL import Image

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg  # noqa: E402


APP = Path(__file__).resolve().parents[1]
PUBLIC = APP / "frontend-vue" / "public"
BRAND = PUBLIC / "brand"
ICONS = APP / "src-tauri" / "icons"
PACKAGE = APP / "assets" / "adito-assets.zip"
GUIDE = APP.parent / "docs" / "design" / "Assets-visuais-Adito.md"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def svg_png(source: Path, target: Path, width: int, height: int | None = None) -> None:
    """Exporta uma composição SVG com a arte original incorporada."""
    height = height or width
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    handle = Rsvg.Handle.new_from_file(str(source))
    viewport = Rsvg.Rectangle()
    viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, width, height
    handle.render_document(context, viewport)
    stream = io.BytesIO()
    surface.write_to_png(stream)
    stream.seek(0)
    with Image.open(stream) as image:
        image.convert("RGBA").save(target, optimize=True)


def original_image(parent: ET.Element, source: Path, **attributes: str) -> None:
    """Incorpora o arquivo original sem reinterpretar cores ou transparência."""
    ET.SubElement(parent, f"{{{SVG_NS}}}image", {
        **attributes,
        "href": "data:image/png;base64," + base64.b64encode(source.read_bytes()).decode("ascii"),
    })


def symbol_svg(theme: str) -> None:
    source = BRAND / f"adito-{theme}.png"
    with Image.open(source) as image:
        width, height = image.size
    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}"
    })
    ET.SubElement(root, f"{{{SVG_NS}}}title").text = "Adito"
    ET.SubElement(root, f"{{{SVG_NS}}}desc").text = (
        "Arte PNG original incorporada sem perdas, preservando cores e transparência."
    )
    original_image(root, source, width=str(width), height=str(height))
    ET.indent(root)
    ET.ElementTree(root).write(BRAND / f"adito-{theme}.svg", encoding="unicode")


def register_font() -> None:
    """Usa a IBM Plex Sans já distribuída com o app ao contornar o wordmark."""
    fontconfig = ctypes.CDLL("libfontconfig.so.1")
    fontconfig.FcConfigGetCurrent.restype = ctypes.c_void_p
    fontconfig.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    font = PUBLIC / "fonts" / "ibm-plex-5.ttf"
    if not fontconfig.FcConfigAppFontAddFile(
        fontconfig.FcConfigGetCurrent(), str(font).encode()
    ):
        raise RuntimeError(f"Não foi possível carregar a fonte: {font}")


def logo_svg(theme: str) -> Path:
    """Combina a arte original com o nome em caminhos, sem fontes externas."""
    buffer = io.BytesIO()
    surface = cairo.SVGSurface(buffer, 880, 320)
    context = cairo.Context(surface)
    context.select_font_face("IBM Plex Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    context.set_font_size(208)
    context.move_to(344, 233)
    context.text_path("Adito")
    context.fill()
    surface.finish()
    wordmark = ET.fromstring(buffer.getvalue())
    logo = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": "880", "height": "320", "viewBox": "0 0 880 320", "fill": "none"
    })
    ET.SubElement(logo, f"{{{SVG_NS}}}title").text = "Adito"
    original_image(logo, BRAND / f"adito-{theme}.png", x="16", y="16", width="288", height="288")
    color = "#1F302B" if theme == "light" else "#F0F4F1"
    for child in wordmark:
        for path in child.iter(f"{{{SVG_NS}}}path"):
            path.set("fill", color)
        logo.append(child)
    target = BRAND / f"logo-adito-{theme}.svg"
    ET.indent(logo)
    ET.ElementTree(logo).write(target, encoding="unicode", xml_declaration=False)
    return target


def theme_favicon() -> None:
    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": "64", "height": "64", "viewBox": "0 0 1254 1254"
    })
    ET.SubElement(root, f"{{{SVG_NS}}}title").text = "Adito"
    original_image(root, BRAND / "adito-light.png", width="1254", height="1254", id="light")
    original_image(root, BRAND / "adito-dark.png", width="1254", height="1254", id="dark")
    style = ET.SubElement(root, f"{{{SVG_NS}}}style")
    style.text = """#dark { display: none; }
    @media (prefers-color-scheme: dark) {
      #light { display: none; }
      #dark { display: inline; }
    }"""
    ET.indent(root)
    ET.ElementTree(root).write(PUBLIC / "favicon.svg", encoding="unicode")


def export_assets() -> None:
    register_font()
    ICONS.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        symbol_svg(theme)
        with Image.open(BRAND / f"adito-{theme}.png") as image:
            image.resize((1024, 1024), Image.Resampling.LANCZOS).save(
                BRAND / f"adito-{theme}-1024.png", optimize=True
            )
        logo = logo_svg(theme)
        svg_png(logo, BRAND / f"logo-adito-{theme}.png", 880, 320)
        svg_png(logo, BRAND / f"logo-adito-{theme}@2x.png", 1760, 640)
    theme_favicon()
    for name, size in {
        "favicon.png": 32, "favicon-16x16.png": 16,
        "favicon-32x32.png": 32, "apple-touch-icon.png": 180,
    }.items():
        with Image.open(BRAND / "adito-light.png") as image:
            image.resize((size, size), Image.Resampling.LANCZOS).save(PUBLIC / name, optimize=True)
    with Image.open(BRAND / "adito-light.png") as image:
        image.save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # Os ícones Tauri distribuídos pelo projeto já têm as resoluções exigidas.
    # Mantê-los evita substituir sua arte/paleta por outra interpretação.
    for name in ("32x32.png", "128x128.png", "128x128@2x.png", "icon.png", "icon.ico", "icon.icns"):
        if not (ICONS / name).is_file():
            raise FileNotFoundError(f"Ícone Tauri original ausente: {ICONS / name}")
    files = sorted([
        *BRAND.glob("*.svg"), *BRAND.glob("*.png"),
        *PUBLIC.glob("favicon*"), PUBLIC / "apple-touch-icon.png", *ICONS.glob("*"),
    ])
    manifest = []
    for path in files:
        item: dict = {"path": str(path.relative_to(APP)), "bytes": path.stat().st_size}
        if path.suffix == ".svg":
            root = ET.parse(path).getroot()
            item["viewBox"] = root.attrib["viewBox"]
        else:
            with Image.open(path) as image:
                image.load()
                item.update(format=image.format, width=image.width, height=image.height, mode=image.mode)
                if path.suffix == ".ico":
                    item["sizes"] = sorted(image.ico.sizes())
                    for size in image.ico.sizes():
                        image.ico.getimage(size).load()
                if path.suffix == ".icns":
                    item["sizes"] = image.info["sizes"]
                    for size in image.info["sizes"]:
                        image.icns.getimage(size).load()
        manifest.append(item)
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PACKAGE, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, str(path.relative_to(APP)))
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        if GUIDE.is_file():
            archive.write(GUIDE, "LEIA-ME.md")
    print(f"{len(files)} assets exportados e verificados: {PACKAGE}")


if __name__ == "__main__":
    export_assets()
