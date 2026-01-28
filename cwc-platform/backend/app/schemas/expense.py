"""Pydantic schemas for expense tracking."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ Expense Category Schemas ============

class ExpenseCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#6b7280", pattern=r"^#[0-9a-fA-F]{6}$")
    icon: Optional[str] = None
    is_tax_deductible: bool = True


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    icon: Optional[str] = None
    is_tax_deductible: Optional[bool] = None
    is_active: Optional[bool] = None


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Expense Schemas ============

class ExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    expense_date: date
    category_id: Optional[str] = None
    vendor: Optional[str] = Field(None, max_length=200)
    payment_method: str = Field(default="card")
    reference: Optional[str] = Field(None, max_length=100)
    receipt_url: Optional[str] = None
    is_tax_deductible: bool = True
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    is_recurring: bool = False
    recurring_expense_id: Optional[str] = None


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    category_id: Optional[str] = None
    vendor: Optional[str] = Field(None, max_length=200)
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    receipt_url: Optional[str] = None
    is_tax_deductible: Optional[bool] = None
    notes: Optional[str] = None


class ExpenseRead(ExpenseBase):
    id: str
    tax_year: int
    is_recurring: bool
    recurring_expense_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    category: Optional[ExpenseCategoryRead] = None

    class Config:
        from_attributes = True


class ExpenseList(BaseModel):
    items: List[ExpenseRead]
    total: int
    page: int
    size: int


# ============ Recurring Expense Schemas ============

class RecurringExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    vendor: Optional[str] = Field(None, max_length=200)
    category_id: Optional[str] = None
    frequency: str = Field(default="monthly")  # weekly, monthly, quarterly, yearly
    start_date: date
    end_date: Optional[date] = None
    auto_create: bool = False
    reminder_days: int = Field(default=3, ge=0, le=30)
    notes: Optional[str] = None


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0)
    vendor: Optional[str] = None
    category_id: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    auto_create: Optional[bool] = None
    reminder_days: Optional[int] = Field(None, ge=0, le=30)
    notes: Optional[str] = None


class RecurringExpenseRead(RecurringExpenseBase):
    id: str
    next_due_date: date
    last_generated_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ExpenseCategoryRead] = None

    class Config:
        from_attributes = True


# ============ Mileage Schemas ============

class MileageLogBase(BaseModel):
    trip_date: date
    description: str = Field(..., min_length=1, max_length=500)
    purpose: str = Field(default="client_meeting")
    miles: Decimal = Field(..., gt=0)
    start_location: Optional[str] = Field(None, max_length=200)
    end_location: Optional[str] = Field(None, max_length=200)
    round_trip: bool = False
    contact_id: Optional[str] = None
    notes: Optional[str] = None


class MileageLogCreate(MileageLogBase):
    rate_per_mile: Optional[Decimal] = None  # If not provided, use current year rate


class MileageLogUpdate(BaseModel):
    trip_date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    purpose: Optional[str] = None
    miles: Optional[Decimal] = Field(None, gt=0)
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    round_trip: Optional[bool] = None
    contact_id: Optional[str] = None
    notes: Optional[str] = None


class MileageLogRead(MileageLogBase):
    id: str
    rate_per_mile: Decimal
    total_deduction: Decimal
    tax_year: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MileageLogList(BaseModel):
    items: List[MileageLogRead]
    total: int


# ============ Contractor Schemas ============

class ContractorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    business_name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=20)
    tax_id_type: str = Field(default="ein")
    w9_on_file: bool = False
    w9_received_date: Optional[date] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    service_type: Optional[str] = None
    notes: Optional[str] = None


class ContractorCreate(ContractorBase):
    pass


class ContractorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    tax_id_type: Optional[str] = None
    w9_on_file: Optional[bool] = None
    w9_received_date: Optional[date] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    service_type: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContractorRead(ContractorBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_paid_ytd: Optional[Decimal] = None  # Computed field

    class Config:
        from_attributes = True


class ContractorList(BaseModel):
    items: List[ContractorRead]
    total: int


# ============ Contractor Payment Schemas ============

class ContractorPaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_date: date
    description: str = Field(..., min_length=1, max_length=500)
    payment_method: str = Field(default="bank_transfer")
    reference: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None
    notes: Optional[str] = None


class ContractorPaymentCreate(ContractorPaymentBase):
    contractor_id: str
    create_expense: bool = True  # Also create matching expense record


class ContractorPaymentUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_date: Optional[date] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None
    notes: Optional[str] = None


class ContractorPaymentRead(ContractorPaymentBase):
    id: str
    contractor_id: str
    expense_id: Optional[str]
    tax_year: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Report Schemas ============

class ExpenseSummary(BaseModel):
    total_expenses: Decimal
    total_deductible: Decimal
    by_category: List[dict]  # [{category, amount, count}]
    by_month: List[dict]  # [{month, amount}]


class MileageSummary(BaseModel):
    total_miles: Decimal
    total_deduction: Decimal
    trip_count: int
    by_purpose: List[dict]  # [{purpose, miles, amount}]


class ContractorSummary(BaseModel):
    contractor_id: str
    contractor_name: str
    total_paid: Decimal
    payment_count: int
    needs_1099: bool  # True if total >= $600


class ProfitLossReport(BaseModel):
    period_start: date
    period_end: date
    # Revenue
    total_revenue: Decimal
    invoices_paid: int
    # Expenses
    total_expenses: Decimal
    expenses_by_category: List[dict]
    # Mileage
    total_mileage_deduction: Decimal
    # Contractor payments
    total_contractor_payments: Decimal
    # Net
    net_profit: Decimal
    profit_margin: Optional[Decimal]


class TaxSummary(BaseModel):
    tax_year: int
    # Income
    gross_income: Decimal
    # Deductions
    total_expenses: Decimal
    mileage_deduction: Decimal
    contractor_payments: Decimal
    total_deductions: Decimal
    # Estimated taxable
    estimated_taxable_income: Decimal
    # Quarterly breakdown
    quarters: List[dict]  # [{quarter, income, expenses}]
    # 1099 contractors
    contractors_needing_1099: List[ContractorSummary]
