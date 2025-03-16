from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend import services
from backend.database import get_db
from backend.schemas import TransportTable


router = APIRouter(prefix="/tables", tags=["tables"])


@router.get('/')
def get_tables(db: Session = Depends(get_db)):
    return services.get_tables(db)


@router.get('/{table_id}')
def get_table(table_id: int):
    pass


@router.post('/create')
def create_table(table: TransportTable, db: Session = Depends(get_db)):
    return services.create_table(table, db)


@router.post('create_basic_plan/{table_id}')
def create_basic_plan(table_id: int):
    pass


@router.post('create_optimal_plan/{table_id}')
def create_optimal_plan(table_id: int):
    pass


@router.get('last_basic_plan/{table_id}')
def get_table_last_basic_plan(table_id: int):
    pass


@router.get('last_optimal_plan/{table_id}')
def get_table_last_optimal_plan(table_id: int):
    pass
