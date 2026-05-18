import base64
import logging
import os
import subprocess
from pathlib import Path

from openai import OpenAI
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ColoringBookImageGenerator:
    """
    Generates coloring book style images from input images using OpenAI's image generation API.
    Converts the result into a cleaned black-line PNG and an SVG vector format.
    """

    def __init__(self, api_key: str, media_dir: str = "./core/media"):
        """
        Initialize the image generator with API credentials and media output paths.

        param api_key: OpenAI API key.
        param media_dir: Base directory to store outputs.
        """
        self.client = OpenAI(api_key=api_key)
        self.media_dir = media_dir
        self.output_dir = os.path.join(self.media_dir, "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_file(self, file_path: str) -> str:
        """
        Uploads a file to OpenAI and returns the file ID.

        param file_path: Path to the image file.
        return: OpenAI file ID.
        """
        with open(file_path, "rb") as f:
            result = self.client.files.create(file=f, purpose="vision")
        return result.id

    def _keep_black_lines_only(self, image_path: str, output_path: str, threshold: int = 80) -> None:
        """
        Filters the input image to keep only black lines (based on threshold) and makes background transparent.

        param image_path: Input PNG file path.
        param output_path: Output cleaned PNG file path.
        param threshold: RGB threshold to determine black lines.
        """
        image = Image.open(image_path).convert("RGBA")
        width, height = image.size
        pixels = image.load()
        if pixels is None:
            raise RuntimeError("Failed to load pixels from image")

        for y in range(height):
            for x in range(width):
                rgba = pixels[x, y]
                if not isinstance(rgba, tuple) or len(rgba) != 4:
                    raise ValueError(f"Unexpected pixel format at ({x},{y}): {rgba}")
                r, g, b, a = rgba
                if r < threshold and g < threshold and b < threshold:
                    pixels[x, y] = (0, 0, 0, 255)
                else:
                    pixels[x, y] = (255, 255, 255, 0)

        image.save(output_path, format="PNG")

    def _invert_svg_strokes(self, svg_path: str) -> None:
        with open(svg_path, encoding="utf-8") as f:
            content = f.read()

        content = content.replace('stroke="#000000"', 'stroke="#ffffff"')
        content = content.replace('fill="#000000"', 'fill="#ffffff"')

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _png_to_svg(self, png_path: str, svg_path: str) -> None:
        """
        Converts a cleaned PNG image to SVG using ImageMagick and Potrace.

        param png_path: Input cleaned PNG image path.
        param svg_path: Output SVG file path.
        """
        png = str(Path(png_path).resolve())
        svg = str(Path(svg_path).resolve())

        convert_cmd = [
            "convert",
            png,
            "-threshold", "50%",
            "-flatten",
            "-colorspace", "gray",
            "bmp:-"
        ]

        potrace_cmd = [
            "potrace",
            "-s",
            "-o", svg
        ]

        try:
            convert_proc = subprocess.Popen(convert_cmd, stdout=subprocess.PIPE)
            result = subprocess.run(potrace_cmd, stdin=convert_proc.stdout, check=True, capture_output=True, text=True)
            logger.info(f"Potrace output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Potrace trace failed: {e.stderr}")
            raise

    def generate_image(self, input_image_path: str) -> str | None:
        """
        Main method to process an input image into a coloring book SVG.
        Steps:
          - Upload image to OpenAI
          - Generate coloring-style image
          - Clean black lines
          - Convert to SVG

        param input_image_path: Path to the user-supplied image.
        return: SVG output path or None if generation fails.
        """
        try:
            file_id = self._create_file(input_image_path)
            prompt = "Transform it to a coloring book image with a resolution of 1024x1024"

            response = self.client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "file_id": file_id},
                        ],
                    }
                ],
                tools=[{"type": "image_generation"}],
            )

            image_generation_calls = [
                output
                for output in response.output
                if output.type == "image_generation_call"
            ]

            if not image_generation_calls:
                logger.warning("No image generation result.")
                return None

            raw_output_path = os.path.join(self.output_dir, "output_raw.png")
            clean_output_path = os.path.join(self.output_dir, "output_clean.png")
            svg_output_path = os.path.join(self.output_dir, "output_clean.svg")

            image_base64 = image_generation_calls[0].result
            if not image_base64:
                raise ValueError("Empty image_base64 received")
            with open(raw_output_path, "wb") as f:
                f.write(base64.b64decode(image_base64))

            self._keep_black_lines_only(raw_output_path, clean_output_path)
            self._png_to_svg(clean_output_path, svg_output_path)
            self._invert_svg_strokes(svg_output_path)

            os.remove(raw_output_path)
            os.remove(clean_output_path)

            return svg_output_path

        except Exception as e:
            logger.exception(f"Image generation failed: {e}")
            return None
