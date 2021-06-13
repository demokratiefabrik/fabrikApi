from cornice.service import Service
from jsonschema import validate

# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE
from fabrikApi.views.lib.factories import AssemblyFactory, StageManagerFactory


def stage_validator(request, **kwargs):
    schema = kwargs['schema']
    data = request.json_body['stage']
    validate(data, schema=schema)


# https://python-jsonschema.readthedocs.io/en/latest/validate/
stage_schema = {
    "type": "object",
    "properties": {
        "disabled": {"type": "boolean", "default": False},
        "title": {"type": "string", "maxLength": 100},
        "type": {"type": "string", "maxLength": 20},
        "info": {"type": "string"},
        "group": {"type": "string"},
        "order_position": {"type": ["number",  "null"]},
        "date_start": {"type": ["string",  "null"], "format": "date-time"},
        "date_end": {"type": ["string",  "null"], "format": "date-time"},
        "custom_data": {"type": ["object",  "null"], "maxLength": 50},
    },
    "required": ["title", "info"]
}


service_stage_id = Service(cors_origins=('*',), 
    name='stage_id', description='Edit / View / Delete an stage.',
    path='/assembly/{assembly_identifier}/stage/{stage_id:\d+}',
    traverse='/{stage_id}',
    factory=StageManagerFactory)

service_stage = Service(cors_origins=('*',), 
    name='stage', description='Creates a blank stage.',
    path='/assembly/{assembly_identifier}/stage',
    traverse='/{assembly_identifier}',
    factory=AssemblyFactory)
