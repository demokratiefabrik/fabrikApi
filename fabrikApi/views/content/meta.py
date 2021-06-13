from cornice.service import Service
from jsonschema import validate

from fabrikApi.views.lib.factories import ContentManagerFactory


def content_validator(request, **kwargs):
    schema = kwargs['schema']
    data = request.json_body['content']
    validate(data, schema=schema)


# "id": {"type": "number"},
content_schema = {
    "type": "object",
    "properties": {
        "parent_id": {"type": ["number", "null"]},
        "title": {"type": "string", "maxLength": 300},
        "comment_title": {"type": "string", "maxLength": 300},
        "disabled": {"type": "boolean", "default": False},
        "type": {"type": "string", "maxLength": 30},
        "text": {"type": "string",  "maxLength": 3000},
    },
    "anyOf": [
        {
            "required": [
                "text"
            ]
        },
        {
            "required": [
                "title"
            ]
        }, 
    ]
    # "required": ["title", "text"]
}

# https://python-jsonschema.readthedocs.io/en/latest/validate/
# contenttree_schema = {
#     "type": "object",
#     "properties": {
#         "disabled": {"type": "boolean", "default" : False},
#         "title": {"type": "string", "maxLength": 100},
#         "info": {"type": "string"},
#         "order_position": {"type":["number",  "null"]},
#         "date_start": {"type": ["string",  "null"], "format": "date-time"},
#         "date_end": {"type": ["string",  "null"], "format": "date-time"},
#         "icon": {"type": ["string",  "null"], "maxLength": 100},
#     },
#     "required": ["title", "info", "disabled"]
# }
