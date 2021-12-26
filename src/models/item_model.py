from tortoise.models import Model
from tortoise import fields


class Item(Model):
    id = fields.IntField(pk=True)
    image = fields.CharField(max_length=255)
    name = fields.CharField(max_length=255)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    subscribers = fields.ManyToManyField("models.User")

    def __str__(self):
        return f"<item [{self.name}]>"
