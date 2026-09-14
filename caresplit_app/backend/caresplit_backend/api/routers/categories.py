from decimal import Decimal

from fastapi import APIRouter, Depends, status

from caresplit_backend.api.auth import get_current_username
from caresplit_backend.api.models import Category, CategoryCreate, CategoryUpdate, category_to_response
from caresplit_backend.api.store import Store, get_store

router = APIRouter(
    prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_username)]
)


@router.get("", response_model=list[Category])
def list_categories(store: Store = Depends(get_store)) -> list[Category]:
    return [category_to_response(c) for c in store.expenses.list_categories()]


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryCreate, store: Store = Depends(get_store)) -> Category:
    category = store.expenses.create_category(body.name, Decimal(body.pct_me), body.notes)
    return category_to_response(category)


@router.patch("/{category_id}", response_model=Category)
def update_category(
    category_id: int, body: CategoryUpdate, store: Store = Depends(get_store)
) -> Category:
    category = store.expenses.update_category(
        category_id,
        name=body.name,
        pct_me=Decimal(body.pct_me) if body.pct_me is not None else None,
        notes=body.notes,
    )
    return category_to_response(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, store: Store = Depends(get_store)) -> None:
    store.expenses.delete_category(category_id)
