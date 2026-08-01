user_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "gender": {"type": "string"},
        "status": {"type": "string"},
    },
    "required": ["id", "name", "email", "gender", "status"],
}

users_list_schema = {
    "type": "array",
    "items": user_schema,
}
