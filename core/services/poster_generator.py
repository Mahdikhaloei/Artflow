import logging
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)

NS: dict[str, str] = {
    "svg": "http://www.w3.org/2000/svg",
    "xlink": "http://www.w3.org/1999/xlink",
}
ET.register_namespace("xlink", NS["xlink"])


def parse_svg_length(length: str) -> float:
    length = length.strip()
    if length.endswith("px"):
        return float(length[:-2])
    if length.endswith("mm"):
        return float(length[:-2]) * 96 / 25.4
    if length.endswith("cm"):
        return float(length[:-2]) * 96 / 2.54
    if length.endswith("in"):
        return float(length[:-2]) * 96
    if length.endswith("pt"):
        return float(length[:-2]) * 96 / 72
    try:
        return float(length)
    except ValueError:
        raise ValueError(f"Cannot parse SVG length: {length}")


class SVGPosterEditor:
    """
    A utility class to edit SVG poster templates by replacing text and embedding external SVG images.
    Also supports exporting the final SVG to PNG format using Inkscape.
    """
    def __init__(
        self,
        input_svg: Path,
        output_svg: Path,
        output_png: Path,
        font: str = "Bungee",
    ) -> None:
        """
        Initialize the editor with file paths and font settings.

        param input_svg: Path to the input SVG template.
        param output_svg: Path to save the modified SVG.
        param output_png: Path to save the exported PNG.
        param font: Font to apply to the inserted text elements.
        """
        self.input_svg = input_svg
        self.output_svg = output_svg
        self.output_png = output_png
        self.font = font
        self.tree = ET.parse(input_svg)
        self.root = self.tree.getroot()
        self.canvas_width, self.canvas_height = self._get_canvas_dimensions()

    def _get_canvas_dimensions(self) -> tuple[float, float]:
        """
        Extracts canvas width and height from the SVG root using width/height or viewBox.

        return: Tuple containing width and height in pixels.
        """
        width_attr = self.root.get("width")
        height_attr = self.root.get("height")
        if width_attr and height_attr:
            return parse_svg_length(width_attr), parse_svg_length(height_attr)
        viewbox = self.root.get("viewBox")
        if viewbox:
            _, _, w, h = map(float, viewbox.strip().split())
            return w, h
        raise ValueError("SVG must have width/height or viewBox")

    def _estimate_text_width(self, text: str, font_size: float) -> float:
        """
        Approximates text width in pixels based on length and font size.

        param text: Text to measure.
        param font_size: Font size in pixels.
        return: Estimated width in pixels.
        """
        return len(text) * font_size * 0.6

    def _set_text_by_id(self, text_id: str, text: str, max_width: float | None) -> None:
        """
        Updates a text element in the SVG by ID, adjusts font size to fit max width.

        param text_id: ID of the <text> element in SVG.
        param text: New text content to insert.
        param max_width: Maximum allowed width for the text block.
        """
        text_elem = self.root.find(f'.//svg:text[@id="{text_id}"]', NS)
        if text_elem is None:
            raise ValueError(f"No <text> element with id '{text_id}'")

        styles = dict(
            item.split(":", 1) for item in text_elem.get("style", "").split(";") if item
        )
        styles["font-family"] = self.font
        base_size = 40.0
        if max_width:
            estimated = self._estimate_text_width(text, base_size)
            if estimated > max_width:
                scale = max_width / estimated
                base_size *= scale
        styles["font-size"] = f"{base_size}px"
        text_elem.set("style", ";".join(f"{k}:{v}" for k, v in styles.items()))

        tspans = list(text_elem.findall("svg:tspan", NS))
        for tsp in tspans:
            text_elem.remove(tsp)
        tspan = ET.Element(f"{{{NS['svg']}}}tspan")
        tspan.text = text
        tspan.set("x", text_elem.get("x", "0"))
        tspan.set("y", text_elem.get("y", "0"))
        text_elem.append(tspan)

    def _insert_svg_image(self, href: Path, target_id: str, target_width: float, target_height: float) -> None:
        """
        Replaces an SVG group with an external SVG file, scaled and positioned in the canvas.

        param href: Path to the external SVG file.
        param target_id: ID of the group to replace in the template.
        param target_width: Desired width of inserted image in pixels.
        param target_height: Desired height of inserted image in pixels.
        """
        group_path = f'.//svg:g[@id="{target_id}"]'
        group = self.root.find(group_path, NS)
        if group is None:
            raise ValueError(f"Group with id '{target_id}' not found")
        parent = self.root.find(f"{group_path}/..", NS)
        if parent is None:
            raise ValueError("Cannot find parent of image group")
        parent.remove(group)

        logger.info(f"Trying to parse SVG file: {href}")
        if not href.exists():
            raise FileNotFoundError(f"SVG file not found: {href}")
        size = href.stat().st_size
        logger.info(f"SVG file size: {size} bytes")
        if size == 0:
            raise ValueError(f"SVG file is empty: {href}")

        try:
            vector_tree = ET.parse(href)
        except ET.ParseError as e:
            logger.error(f"Failed to parse SVG file {href}: {e}")
            raise

        vector_root = vector_tree.getroot()

        width_attr = vector_root.get("width")
        height_attr = vector_root.get("height")
        if width_attr and height_attr:
            src_w = parse_svg_length(width_attr)
            src_h = parse_svg_length(height_attr)
        else:
            vb = vector_root.get("viewBox")
            if not vb:
                raise ValueError("Vector SVG must have width/height or viewBox")
            _, _, src_w, src_h = map(float, vb.strip().split())

        scale_x = target_width / src_w
        scale_y = target_height / src_h

        offset_x = 40
        offset_y = 50

        translate_x = (self.canvas_width - target_width) / 2 + offset_x
        translate_y = (self.canvas_height - target_height) / 2 + offset_y

        wrapper = ET.Element(f"{{{NS['svg']}}}g", {
            "id": "InsertedVector",
            "transform": f"translate({translate_x},{translate_y}) scale({scale_x},{scale_y})"
        })
        for el in list(vector_root):
            wrapper.append(el)
        parent.append(wrapper)
        logger.info(f"Wrapper children: {[el.tag for el in wrapper]}")
        logger.info("Inserted image at center.")

    def _convert_svg_to_png(self, svg_path: str, png_path) -> None:
        """
        Converts an SVG file to PNG using Inkscape in headless mode.

        param svg_path: Path to the SVG file.
        param png_path: Output PNG path.
        """
        svg = Path(svg_path)
        out = Path(png_path)

        if not svg.exists():
            raise FileNotFoundError(f"svg not found {svg}")

        subprocess.run([
            "xvfb-run", "inkscape",
            str(svg),
            f"--export-filename={out}",
            "--export-type=png",
            "--export-background-opacity=0"
        ], check=True, capture_output=True, text=True)

        logging.info(f"converted {svg} -> {out}")
        os.remove(svg)

    def compose(
        self,
        replacements: dict[str, str],
        max_widths: dict[str, float] | None = None,
        image_info: dict[str, str] | None = None
    ) -> None:
        """
        Applies text replacements and optional image insertion, writes final SVG and PNG.

        param replacements: Dictionary mapping text IDs to replacement values.
        param max_widths: Optional dictionary mapping text IDs to maximum widths.
        param image_info: Optional dictionary with keys for SVG image insertion.
        """
        for text_id, text in replacements.items():
            self._set_text_by_id(
                text_id,
                text,
                max_widths[text_id] if max_widths and text_id in max_widths else None
            )

        if image_info:
            self._insert_svg_image(
                href=Path(image_info["href"]),
                target_id=image_info["target_id"],
                target_width=float(image_info["width"]),
                target_height=float(image_info["height"]),
            )

        self.output_svg.parent.mkdir(parents=True, exist_ok=True)
        self.tree.write(self.output_svg, encoding="utf-8", xml_declaration=True)
        logger.info("Final SVG poster written to %s", self.output_svg)

        self._convert_svg_to_png(str(self.output_svg), str(self.output_png))
