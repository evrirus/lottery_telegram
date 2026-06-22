from tortoise import Tortoise
from tortoise import models, fields

from config import TORTOISE_ORM

DB_PATH = "lottery.db"

DB_URL = "sqlite://lottery.db"

async def init_tortoise():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


class User(models.Model):
    id = fields.IntField(pk=True)

    # Telegram ID должен быть уникальным
    telegram_id = fields.BigIntField(unique=True, index=True)

    # Баланс (Decimal хранится как string внутри SQLite)
    balance = fields.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Дата регистрации
    register_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User({self.id}, tg={self.telegram_id}, balance={self.balance})"


class Lottery(models.Model):
    id = fields.IntField(pk=True)

    prize = fields.TextField()
    ticket_price = fields.IntField()

    total_tickets = fields.IntField()
    sold_tickets = fields.IntField(default=0)

    channel_id = fields.BigIntField()

    status = fields.CharField(max_length=20, default="active")
    winner_user_id = fields.BigIntField(null=True)

    class Meta:
        table = "lotteries"


class Ticket(models.Model):
    id = fields.IntField(pk=True)

    lottery = fields.ForeignKeyField("models.Lottery", related_name="tickets", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="tickets", on_delete=fields.CASCADE)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tickets"

