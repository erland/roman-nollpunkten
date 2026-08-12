#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "epub": "http://www.idpf.org/2007/ops",
}
ET.register_namespace("", NS["opf"])

def find_container_root(container_xml: Path) -> Path:
    tree = ET.parse(container_xml)
    rootfile = tree.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    if rootfile is None:
        raise RuntimeError("EPUB container saknar rootfile.")
    return Path(rootfile.attrib["full-path"])

def split_chapter_headings(epub_dir: Path) -> int:
    changed = 0
    pattern = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
    for xhtml in epub_dir.rglob("*.xhtml"):
        tree = ET.parse(xhtml)
        root = tree.getroot()
        local_changed = False
        for h1 in root.findall(".//xhtml:h1", NS):
            text = "".join(h1.itertext()).strip()
            match = pattern.match(text)
            if not match:
                continue
            ident = h1.attrib.get("id")
            h1.clear()
            if ident:
                h1.set("id", ident)
            n = ET.SubElement(h1, f"{{{NS['xhtml']}}}span", {"class": "chapter-number"})
            n.text = match.group(1)
            t = ET.SubElement(h1, f"{{{NS['xhtml']}}}span", {"class": "chapter-title"})
            t.text = match.group(2)
            local_changed = True
        if local_changed:
            tree.write(xhtml, encoding="utf-8", xml_declaration=True)
            changed += 1
    return changed

def clean_custom_title_page(epub_dir: Path) -> int:
    """Remove Pandoc's duplicated H1 above the custom title-page block."""
    changed = 0
    for xhtml in epub_dir.rglob("*.xhtml"):
        tree = ET.parse(xhtml)
        root = tree.getroot()
        parent_map = {child: parent for parent in root.iter() for child in parent}
        local_changed = False
        for section in root.findall(".//xhtml:section[@class='title-page']", NS):
            parent = parent_map.get(section)
            if parent is None:
                continue
            for child in list(parent):
                if child.tag == f"{{{NS['xhtml']}}}h1" and "unnumbered" in child.attrib.get("class", "").split():
                    parent.remove(child)
                    local_changed = True
        if local_changed:
            tree.write(xhtml, encoding="utf-8", xml_declaration=True)
            changed += 1
    return changed

def find_title_page_hrefs(epub_dir: Path, opf_rel: Path) -> set[str]:
    """Find XHTML files containing the custom title-page block.

    Pandoc can change filenames between versions, so do not assume ch001.xhtml.
    Return hrefs relative to the nav file directory when possible.
    """
    opf_path = epub_dir / opf_rel
    manifest_tree = ET.parse(opf_path)
    manifest_root = manifest_tree.getroot()
    manifest = manifest_root.find("opf:manifest", NS)
    if manifest is None:
        return set()

    title_paths: set[Path] = set()
    for xhtml in epub_dir.rglob("*.xhtml"):
        try:
            tree = ET.parse(xhtml)
        except ET.ParseError:
            continue
        root = tree.getroot()
        if root.find(".//xhtml:section[@class='title-page']", NS) is not None:
            title_paths.add(xhtml.resolve())

    hrefs: set[str] = set()
    for item in manifest.findall("opf:item", NS):
        media_type = item.attrib.get("media-type", "")
        href = item.attrib.get("href", "")
        if media_type != "application/xhtml+xml" or not href:
            continue
        item_path = (opf_path.parent / href).resolve()
        if item_path in title_paths:
            hrefs.add(href)
            hrefs.add(Path(href).name)
    return hrefs

def clean_nav_and_spine(epub_dir: Path, opf_rel: Path) -> tuple[bool, int]:
    opf_path = epub_dir / opf_rel
    tree = ET.parse(opf_path)
    root = tree.getroot()
    manifest = root.find("opf:manifest", NS)
    spine = root.find("opf:spine", NS)
    if manifest is None or spine is None:
        raise RuntimeError("EPUB OPF saknar manifest eller spine.")

    nav_items = [
        item for item in manifest.findall("opf:item", NS)
        if "nav" in item.attrib.get("properties", "").split()
    ]
    nav_ids = {item.attrib["id"] for item in nav_items}
    spine_changed = False
    for itemref in spine.findall("opf:itemref", NS):
        if itemref.attrib.get("idref") in nav_ids and itemref.attrib.get("linear") != "no":
            itemref.set("linear", "no")
            spine_changed = True
    if spine_changed:
        tree.write(opf_path, encoding="utf-8", xml_declaration=True)

    title_page_hrefs = find_title_page_hrefs(epub_dir, opf_rel)
    removed = 0

    for nav_item in nav_items:
        nav_path = opf_path.parent / nav_item.attrib["href"]
        nav_tree = ET.parse(nav_path)
        nav_root = nav_tree.getroot()
        parent_map = {child: parent for parent in nav_root.iter() for child in parent}
        nav_removed = 0

        for anchor in list(nav_root.findall(".//xhtml:nav[@epub:type='toc']//xhtml:a", NS)):
            href = anchor.attrib.get("href", "")
            href_without_fragment = href.split("#", 1)[0]
            href_name = Path(href_without_fragment).name
            is_title_page = (
                href_without_fragment in title_page_hrefs
                or href_name in title_page_hrefs
            )
            if not is_title_page:
                continue

            li = parent_map.get(anchor)
            if li is None:
                continue
            ol = parent_map.get(li)
            if ol is None:
                continue
            ol.remove(li)
            removed += 1
            nav_removed += 1

        if nav_removed:
            nav_tree.write(nav_path, encoding="utf-8", xml_declaration=True)

    return spine_changed, removed

def repack(epub_dir: Path, output: Path) -> None:
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w") as z:
        mimetype = epub_dir / "mimetype"
        z.write(mimetype, "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(epub_dir.rglob("*")):
            if not path.is_file() or path == mimetype:
                continue
            z.write(path, path.relative_to(epub_dir).as_posix(), compress_type=zipfile.ZIP_DEFLATED)

def main() -> int:
    if len(sys.argv) != 2:
        print("Användning: fix-epub-after-pandoc.py <fil.epub>", file=sys.stderr)
        return 2
    epub = Path(sys.argv[1]).resolve()
    if not epub.exists():
        raise FileNotFoundError(epub)

    with tempfile.TemporaryDirectory(prefix="fix-epub-") as tmp:
        unpacked = Path(tmp)
        with zipfile.ZipFile(epub) as z:
            z.extractall(unpacked)
        opf_rel = find_container_root(unpacked / "META-INF/container.xml")
        headings = split_chapter_headings(unpacked)
        title_pages = clean_custom_title_page(unpacked)
        nav_changed, nav_removed = clean_nav_and_spine(unpacked, opf_rel)
        repack(unpacked, epub)

    print(
        f"Efterbearbetad EPUB: {headings} kapitelfiler, "
        f"{title_pages} titelsida, nav linear=no: {nav_changed}, "
        f"borttagna titelsideposter i TOC: {nav_removed}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
