from datetime import datetime, timezone

import factory
from core.extensions import db
from core.models.poster import PosterRequest
from factory.alchemy import SQLAlchemyModelFactory


class PosterRequestFactory(SQLAlchemyModelFactory):
    class Meta:
        model = PosterRequest
        sqlalchemy_session = db.session

    text_subtitle = "Sample subtitle"
    reward_amount = "1000"
    image_path = "/some/path/to/image.png"
    rendered_image_path = "/some/path/to/rendered.png"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
