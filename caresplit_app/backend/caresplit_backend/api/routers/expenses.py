from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from caresplit_backend.api.auth import get_current_username
from caresplit_backend.api.models import Expense, ExpenseCreate, ExpenseUpdate, expense_to_response
from caresplit_backend.api.store import Store, get_store

router = APIRouter(
    prefix="/expenses", tags=["expenses"], dependencies=[Depends(get_current_username)]
)


@router.get("", response_model=list[Expense])
def list_expenses(
    category_id: Optional[int] = Query(default=None, alias="categoryId"),
    store: Store = Depends(get_store),
) -> list[Expense]:
    return [expense_to_response(e) for e in store.expenses.list_expenses(category_id)]


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
def create_expense(body: ExpenseCreate, store: Store = Depends(get_store)) -> Expense:
    expense = store.expenses.create_expense(
        date=body.date,
        category_id=body.category_id,
        amount=Decimal(body.amount),
        description=body.description,
        pct_me=Decimal(body.pct_me) if body.pct_me is not None else None,
        note=body.note,
        receipt_filename=body.receipt_filename,
    )
    return expense_to_response(expense)


@router.patch("/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: int, body: ExpenseUpdate, store: Store = Depends(get_store)
) -> Expense:
    expense = store.expenses.update_expense(
        expense_id,
        date=body.date,
        category_id=body.category_id,
        amount=Decimal(body.amount) if body.amount is not None else None,
        description=body.description,
        pct_me=Decimal(body.pct_me) if body.pct_me is not None else None,
        note=body.note,
        receipt_filename=body.receipt_filename,
    )
    return expense_to_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, store: Store = Depends(get_store)) -> None:
    store.expenses.delete_expense(expense_id)
