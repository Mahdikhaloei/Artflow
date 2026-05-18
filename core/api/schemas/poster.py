from marshmallow import Schema, fields, validate


class PosterRequestSchema(Schema):
    email = fields.Email(required=True)
    text_subtitle = fields.String(validate=validate.Length(max=100))
    reward_amount = fields.String(validate=validate.Length(max=50))


class PosterRequestListSchema(Schema):
    id = fields.String()
    text_subtitle = fields.String()
    reward_amount = fields.String()
    created_at = fields.DateTime()
    image_path = fields.String()
    rendered_image_path = fields.String()
