from datetime import date

from fastapi import APIRouter, Depends, Query

from caresplit_backend.api.auth import get_current_username
from caresplit_backend.api.models import DashboardTotals, dashboard_to_response
from caresplit_backend.api.store import Store, get_store

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_username)]
)


@router.get("", response_model=DashboardTotals)
def get_dashboard(
    today: date = Query(...), store: Store = Depends(get_store)
) -> DashboardTotals:
    return dashboard_to_response(store.expenses.dashboard_totals(today))
