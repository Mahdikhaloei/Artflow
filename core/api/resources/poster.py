import os
import uuid
from datetime import datetime, timezone
from typing import Any

from celery import chain
from core.api.schemas import PosterRequestSchema
from core.api.schemas.poster import PosterRequestListSchema
from core.extensions import db
from core.models.poster import PosterRequest
from core.tasks.poster_tasks import (
    generate_coloring_task, generate_png_poster_task, render_blender_output, send_poster_email_task
)
from flask import current_app, request
from flask_restful import Resource
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename: str) -> bool:
    """
    Checks if the uploaded file has an allowed image extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class PosterRequestResource(Resource):
    """
    Handles listing and creating poster requests via the API.
    """
    def get(self) -> tuple[dict[str, Any], int]:
        """
        Returns a list of all submitted poster requests, ordered by creation time (latest first).
        """
        schema = PosterRequestListSchema(many=True)

        posters = PosterRequest.query.order_by(
            PosterRequest.created_at.desc()
        ).all()

        result = schema.dump(posters)
        return {"results": result}, 200

    def post(self) -> tuple[dict[str, Any], int]:
        """
        Accepts a new poster request with form data and image upload.
        Validates input, saves image, stores request in DB, and triggers the Celery task chain.
        """
        schema = PosterRequestSchema()

        try:
            data = dict(request.form)
            data = schema.load(data)

            image_file = request.files.get("image")
            if not image_file or not image_file.filename or not allowed_file(image_file.filename):
                return {"error": "Invalid or missing image file. Only JPG and PNG allowed."}, 400

            if image_file.content_length > 5 * 1024 * 1024:
                return {"error": "Image file too large (max 5MB)."}, 400

            filename = secure_filename(image_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            upload_folder = os.path.join(current_app.root_path, current_app.config["UPLOADED_PHOTOS_DEST"])
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, unique_filename)
            image_file.save(image_path)

            email = data["email"]
            del data["email"]

            poster = PosterRequest(**data, image_path=image_path, created_at=datetime.now(timezone.utc))
            db.session.add(poster)
            db.session.commit()

            chain(
                generate_coloring_task.s(str(poster.id), image_path) |
                generate_png_poster_task.s(str(poster.id)) |
                render_blender_output.s(str(poster.id)) |
                send_poster_email_task.s(email)
            ).apply_async()

            return {
                "result": "Your request has been registered and an email will be sent after processing."
            }, 201

        except ValidationError as err:
            return {"errors": err.messages}, 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Poster submission failed: {e}")
            return {"error": "Internal server error"}, 500
