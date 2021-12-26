from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)

    def __str__(self):
        return f"<user [{self.id}]>"
