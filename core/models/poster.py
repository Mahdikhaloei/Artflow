import uuid

from core.extensions import db
from sqlalchemy.dialects.postgresql import UUID


class PosterRequest(db.Model):
    __tablename__ = "poster_requests"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_path = db.Column(db.String(255), nullable=False)
    text_subtitle = db.Column(db.String(100), nullable=False)
    reward_amount = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime)
    rendered_image_path = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<PosterRequest(id={self.id}, image='{self.rendered_image_path}')>"
