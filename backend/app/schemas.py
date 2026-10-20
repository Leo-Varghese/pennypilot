from datetime import datetime, date
from decimal import Decimal
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, model_validator

Money = Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=2)]
Nonnegative = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=2)]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
Name = Annotated[str, Field(min_length=1, max_length=100)]

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Credentials(Input):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

class AccountIn(Input):
    name: Name
    type: Literal["cash","savings","current","credit_card","wallet","investment","custom"] = "savings"
    currency: Currency = "INR"
    opening_balance: Decimal = Field(default=Decimal(0), max_digits=20, decimal_places=2)
    opening_date: date = Field(default_factory=date.today)

class CategoryIn(Input):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    parent_id: str | None = None

class TransactionIn(Input):
    kind: Literal["income","expense","transfer","refund","adjustment"]
    amount: Money
    currency: Currency = "INR"
    occurred_at: datetime
    account_id: str
    destination_id: str | None = None
    category_id: str | None = None
    merchant: str = Field(default="", max_length=160)
    payment_method: Literal["upi","cash","debit_card","credit_card","wallet","bank_transfer","other"] = "upi"
    location: str = Field(default="", max_length=200)
    purpose: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=5000)
    tags: list[Annotated[str, Field(min_length=1,max_length=50)]] = Field(default_factory=list, max_length=20)
    adjustment_direction: Literal[-1,1] = 1

    @field_validator("occurred_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None: raise ValueError("Include a timezone offset")
        return value

    @model_validator(mode="after")
    def transfer(self):
        if self.kind == "transfer":
            if not self.destination_id or self.destination_id == self.account_id:
                raise ValueError("Transfer requires a different destination account")
            if self.category_id: raise ValueError("Transfers cannot have spending categories")
        elif self.destination_id: raise ValueError("Only transfers have a destination")
        return self

class AllocationIn(Input):
    category_id: str
    amount: Nonnegative

class BudgetIn(Input):
    name: Name
    start_date: date
    end_date: date
    currency: Currency = "INR"
    rollover: bool = False
    previous_id: str | None = None
    allocations: list[AllocationIn] = Field(default_factory=list, max_length=200)
    @model_validator(mode="after")
    def dates(self):
        if self.end_date < self.start_date: raise ValueError("End must follow start")
        if len({a.category_id for a in self.allocations}) != len(self.allocations): raise ValueError("Duplicate category")
        return self

class GoalIn(Input):
    name: Name
    target_amount: Money
    currency: Currency = "INR"
    target_date: date | None = None
    priority: int = Field(default=2, ge=1, le=5)

class ContributionIn(Input):
    amount: Money
    date: date
    note: str = Field(default="", max_length=300)

class RecurringIn(Input):
    name: Name
    kind: Literal["income","expense"] = "expense"
    amount: Money
    currency: Currency = "INR"
    account_id: str
    category_id: str | None = None
    next_due: date
    frequency: Literal["daily","weekly","monthly","quarterly","yearly"] = "monthly"
    active: bool = True

class HoldingIn(Input):
    name: Name
    kind: Literal["asset","liability"]
    amount: Nonnegative
    currency: Currency = "INR"
    valued_on: date

class PreferenceIn(Input):
    currency: Currency = "INR"
    timezone: str = "Asia/Kolkata"
    zero_based: bool = False
    @field_validator("timezone")
    @classmethod
    def zone(cls, value):
        try: ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError): raise ValueError("Unknown IANA timezone")
        return value

class BulkIn(Input):
    ids: list[str] = Field(min_length=1,max_length=200)
    category_id: str | None = None

class PayIn(Input):
    due_date: date
