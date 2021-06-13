from cornice.service import Service
from jsonschema import validate

# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE
from fabrikApi.views.lib.factories import AssemblyFactory


def assembly_validator(request, **kwargs):
    schema = kwargs['schema']
    data = request.json_body['assembly']
    validate(data, schema=schema)


# https://python-jsonschema.readthedocs.io/en/latest/validate/
assembly_schema = {
    "type": "object",
    "properties": {
        "disabled": {"type": "boolean", "default": False},
        "title": {"type": "string", "maxLength": 100},
        "type": {"type": "string", "maxLength": 20},
        "info": {"type": "string"},
        "background": {"type": "string"},
        "date_start": {"type": ["string",  "null"], "format": "date-time"},
        "date_end": {"type": ["string",  "null"], "format": "date-time"},
        "custom_data": {"type": ["object",  "null"], "maxLength": 50},
    },
    "required": ["title", "info"]
}

service_assembly_form_id = Service(cors_origins=('*',), 
    name='assembly_form_id', description='Edit / View / Delete an assembly.',
    path='/assembly/{assembly_identifier}/assembly/form/{assembly_id:\d+}',
    traverse='/{assembly_identifier}',
    factory=AssemblyFactory)

# NOT YET IMPLEMENTED: adding assemblies...
# service_assembly_form = Service(cors_origins=('*',), 
#     name='assembly_form', description='Creates a blank assembly.',
#     path='/assembly/{assembly_identifier}/form/',
#     traverse='/{assembly_identifier}',
#     factory=AssemblyFactory)
