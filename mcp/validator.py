from jsonschema import validate, ValidationError

def validate_input_against_schema(data, schema):
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)

def validate_output_against_schema(result, schema):
    try:
        validate(instance=result, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)
