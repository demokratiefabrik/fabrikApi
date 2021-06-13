from cornice.service import Service
from jsonschema import validate

# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE
from fabrikApi.views.lib.factories import AssemblyFactory, ContentTreeManagerFactory


def contenttree_validator(request, **kwargs):
    schema = kwargs['schema']
    data = request.json_body['contenttree']
    validate(data, schema=schema)


# https://python-jsonschema.readthedocs.io/en/latest/validate/
contenttree_schema = {
    "type": "object",
    "properties": {
        "disabled": {"type": "boolean", "default" : False},
        "title": {"type": "string", "maxLength": 100},
        "info": {"type": "string"},
        "order_position": {"type":["number",  "null"]},
        "date_start": {"type": ["string",  "null"], "format": "date-time"},
        "date_end": {"type": ["string",  "null"], "format": "date-time"},
        "icon": {"type": ["string",  "null"], "maxLength": 100},
    },
    "required": ["title", "info", "disabled"]
}



service_contenttree_id = Service(cors_origins=('*',), 
    name='contenttree_id', description='Edit / View / Delete an contenttree.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)

service_contenttree = Service(cors_origins=('*',), 
    name='contenttree', description='Creates a blank contenttree.',
    path='/assembly/{assembly_identifier}/contenttree',
    traverse='/{assembly_identifier}',
    factory=AssemblyFactory)

service_contenttree_update = Service(cors_origins=('*',), 
    name='contenttree_id_update', 
    description='Load modified and newly added content.',
    path='/assembly/{assembly_identifier}/update22222222/{contenttree_id:\d+}',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)
