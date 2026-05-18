import logging
import os
import uuid
from pathlib import Path

from celery import shared_task
from core.extensions import db
from core.models.poster import PosterRequest
from core.services.blender.blender_mapper import BlenderImageMapper
from core.services.notification.mail.factory import get_default_email_backend
from core.services.open_ai import ColoringBookImageGenerator
from core.services.poster_generator import SVGPosterEditor
from flask import current_app

logger = logging.getLogger(__name__)


@shared_task
def generate_coloring_task(poster_id: str, image_path: str) -> str:
    """
    Generates a coloring book style SVG image using OpenAI from the uploaded image.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    generator = ColoringBookImageGenerator(api_key=api_key)

    output_path = generator.generate_image(image_path)
    if not output_path:
        raise Exception(f"Coloring image generation failed for poster {poster_id}")

    return output_path


@shared_task
def generate_png_poster_task(
    vector_path: str,
    poster_id: str
) -> str:
    """
    Composes a final poster by inserting text and vector image into an SVG template, then exports it as PNG.
    """
    poster = PosterRequest.query.get(poster_id)
    if not poster:
        raise Exception(f"Poster {poster_id} not found")

    template_path = Path(current_app.root_path) / "static" / "posters" / "bitmapp.svg"
    output_dir = Path(current_app.root_path) / "media" / "outputs"

    output_svg = output_dir / f"poster_{poster_id}.svg"
    output_png = output_dir / f"poster_{poster_id}.png"

    editor = SVGPosterEditor(
        input_svg=Path(template_path),
        output_svg=output_svg,
        output_png=output_png,
        font="Bungee",
    )

    try:
        editor.compose(
            replacements={
                "text1": poster.text_subtitle,
                "text2": poster.reward_amount,
            },
            max_widths={
                "text1": 250,
                "text2": 200,
            },
            image_info={
                "target_id": "Photo_Vector",
                "href": vector_path,
                "width": 300,
                "height": 300,
            }
        )
        logger.info(f"SVG poster successfully generated for poster {poster_id}")
        os.remove(vector_path)

        return str(output_png)

    except Exception as e:
        logger.exception(f"SVG poster generation failed for poster {poster_id}: {e}")
        raise


@shared_task
def render_blender_output(image_path: str, poster_id: str) -> str:
    """
    Renders a 3D product mockup using Blender and saves the output path to the database.
    """
    poster = PosterRequest.query.get(poster_id)
    if not poster:
        raise Exception(f"Poster {poster_id} not found")

    filename = f"{poster_id}_{uuid.uuid4().hex}.png"
    output_path = f"./core/media/blender_outputs/{filename}"
    model_path = "./core/static/blender_models/mug.blend"

    mapper = BlenderImageMapper(image_path, model_path, output_path)

    try:
        mapper.run()
    except Exception as e:
        logger.error(f"Blender rendering failed: {e}")
        raise

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Rendered image not found at {output_path}")

    poster.rendered_image_path = f"/media/blender_outputs/{filename}"
    db.session.commit()

    return poster.rendered_image_path


@shared_task
def send_poster_email_task(image_path: str, email: str) -> None:
    """
    Sends a notification email to the user after poster generation is complete.
    """
    if not email:
        logger.warning("No email provided for sending poster")
        return

    try:
        mail_backend = get_default_email_backend()
        mail_backend.send(to_email=email)
        logger.info(f"Poster email sent to {email}")
    except Exception as e:
        logger.exception(f"Failed to send email to {email}: {e}")
