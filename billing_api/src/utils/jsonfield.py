import json
from typing import Optional, Union

from tortoise.exceptions import FieldError
from tortoise.fields import JSONField


class BillingJsonField(JSONField):
    def __init__(self, *args, **kwargs):
        super(JSONField, self).__init__(*args, **kwargs)

    def to_python_value(
            self, value: Optional[Union[str, dict, list]]
    ) -> Optional[Union[dict, list]]:
        if isinstance(value, str):
            try:
                return json.loads(json.loads(value))
            except Exception:
                raise FieldError(f"Value {value} is invalid json value.")

        self.validate(value)
        return value

    def to_db_value(
            self, value: Optional[Union[dict, list, str]], instance: "Union[Type[Model], Model]"
    ) -> Optional[str]:
        self.validate(value)
        if isinstance(value, str):
            try:
                return value
            except Exception:
                raise FieldError(f"Value {value} is invalid json value.")
        return None if value is None else json.dumps(json.dumps(value))
