from core.api.resources import PosterRequestResource
from core.api.schemas import PosterRequestSchema
from core.extensions import apispec
from flask import Blueprint, current_app, jsonify
from flask_restful import Api
from marshmallow import ValidationError

blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)

api.add_resource(PosterRequestResource, "/poster-request/", endpoint="poster-request")


_registered = False


@blueprint.before_app_request
def register_views():
    global _registered
    if _registered:
        return
    apispec.spec.components.schema("PosterRequestSchema", schema=PosterRequestSchema)
    apispec.spec.path(view=PosterRequestResource, app=current_app)
    _registered = True


@blueprint.errorhandler(ValidationError)
def handle_marshmallow_error(e):
    """Return json error for marshmallow validation errors.

    This will avoid having to try/catch ValidationErrors in all endpoints, returning
    correct JSON response with associated HTTP 400 Status (https://tools.ietf.org/html/rfc7231#section-6.5.1)
    """
    return jsonify(e.messages), 400
