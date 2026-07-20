from decimal import Decimal
from enum import Enum

from tortoise import Tortoise
from tortoise import models, fields

from config import TORTOISE_ORM

DB_PATH = "lottery.db"

DB_URL = "sqlite://lottery.db"

async def init_tortoise():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

class LotteryStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"

class User(models.Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, index=True)
    balance = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    register_at = fields.DatetimeField(auto_now_add=True)
    referrer_id = fields.BigIntField(unique=False, index=False, null=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User({self.id}, tg={self.telegram_id}, balance={self.balance})"

    @property
    def balance_display(self) -> str:
        value = self.balance.quantize(Decimal("0.01"))
        return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


class Lottery(models.Model):
    id = fields.IntField(pk=True)

    prize = fields.TextField()
    ticket_price = fields.IntField()

    total_tickets = fields.IntField()
    sold_tickets = fields.IntField(default=0)

    channel_id = fields.BigIntField()
    photo_file_id = fields.CharField(max_length=300, null=True) #todo исправить длину

    status = fields.CharEnumField(
        LotteryStatus,
        default=LotteryStatus.ACTIVE
    )
    # status = fields.CharField(max_length=20)
    winner_user_id = fields.BigIntField(null=True)

    class Meta:
        table = "lotteries"

    @property
    def ticket_price_display(self) -> str:
        return f"{self.ticket_price:,}".replace(",", " ") + " ₽"


class Ticket(models.Model):
    id = fields.IntField(pk=True)

    lottery = fields.ForeignKeyField("models.Lottery", related_name="tickets", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="tickets", on_delete=fields.CASCADE)
    quantity = fields.IntField(default=0)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tickets"
        unique_together = ("lottery", "user")


class PaymentProvider(str, Enum):
    LAVA_SBP = "lava-sbp"  # СБП/Карта
    CRYPTOBOT = "cryptobot"  # Крипто
    TELEGRAM_STARS = "telegram_stars"  # Звёзды ТГ

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Transaction(models.Model):
    id = fields.IntField(pk=True)
    external_payment_id = fields.CharField(max_length=255, null=True, index=True)

    user = fields.ForeignKeyField("models.User", related_name="transactions", on_delete=fields.CASCADE)
    email = fields.CharField(max_length=255, null=True)

    amount = fields.DecimalField(max_digits=15, decimal_places=2)

    provider = fields.CharEnumField(PaymentProvider)
    status = fields.CharEnumField(PaymentStatus, default=PaymentStatus.PENDING)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    completed_at = fields.DatetimeField(null=True)

    metadata = fields.JSONField(default=dict)


