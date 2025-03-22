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
def get_table(table_id: int, db: Session = Depends(get_db)):
    return services.get_table(db, table_id)


@router.post('/create')
def create_table(table: TransportTable, db: Session = Depends(get_db)):
    return services.create_table(db, table)


@router.post('/create_basic_plan/{table_id}')
def create_basic_plan(table_id: int, db: Session = Depends(get_db), mode: int=1):
    return services.create_basic_plan(db, table_id, mode)


@router.post('/create_optimal_plan/{table_id}')
def create_optimal_plan(table_id: int, db: Session = Depends(get_db), mode: int=1):
    return services.create_optimal_plan(db, table_id, mode)


@router.post('/save_solution/{table_id}')
def save_solution(table_id: int, db: Session = Depends(get_db)):
    pass


@router.get('/last_basic_plan/{table_id}')
def get_table_last_basic_plan(table_id: int):
    pass


@router.get('/last_optimal_plan/{table_id}')
def get_table_last_optimal_plan(table_id: int):
    pass
