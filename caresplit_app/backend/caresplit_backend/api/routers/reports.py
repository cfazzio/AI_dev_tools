from fastapi import APIRouter, Depends

from caresplit_backend.api.auth import get_current_username
from caresplit_backend.api.models import YearlyReport, yearly_report_to_response
from caresplit_backend.api.store import Store, get_store

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_username)]
)


# Must be registered before /{year} — otherwise "years" would be parsed as
# the int path parameter and 422 instead of matching this route.
@router.get("/years", response_model=list[int])
def list_available_years(store: Store = Depends(get_store)) -> list[int]:
    return store.expenses.available_years()


@router.get("/{year}", response_model=YearlyReport)
def get_yearly_report(year: int, store: Store = Depends(get_store)) -> YearlyReport:
    return yearly_report_to_response(store.expenses.yearly_report(year))
