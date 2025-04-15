import os
from typing import Optional
from fastapi import APIRouter, Depends, status, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend import services
from backend.database import get_db
from backend.schemas import TransportTable, Solution, User


router = APIRouter(prefix="/tables", tags=["tables"])


@router.get('/', status_code=status.HTTP_200_OK)
def get_tables(user_id: int, db: Session = Depends(get_db)) -> list[TransportTable]:
    return services.get_tables(db, user_id)


@router.get('/{table_id}', status_code=status.HTTP_200_OK)
def get_table(table_id: int, user_id: int, db: Session = Depends(get_db)) -> TransportTable:
    return services.get_table(db, table_id, user_id, is_dummy=False)


@router.post('/create', status_code=status.HTTP_201_CREATED)
def create_table(table: TransportTable, db: Session = Depends(get_db)) -> int:
    return services.create_table(db, table)


@router.post('/create_basic_plan/{table_id}', status_code=status.HTTP_200_OK)
def create_basic_plan(table_id: int, db: Session = Depends(get_db), mode: int=1) -> Solution:
    return services.create_basic_plan(db, table_id, mode)


@router.post('/create_optimal_plan/{table_id}', status_code=status.HTTP_200_OK)
def create_optimal_plan(table_id: int, db: Session = Depends(get_db), mode: int=1) -> Solution:
    return services.create_optimal_plan(db, table_id, mode)


@router.post('/create_basic_plan', status_code=status.HTTP_200_OK)
def create_basic_plan_unauthorized(table: TransportTable, mode: int=1) -> Solution:
    return services.create_basic_plan_unauthorized(table, mode)


@router.post('/create_optimal_plan', status_code=status.HTTP_200_OK)
def create_optimal_plan_unauthorized(table: TransportTable, mode: int=1) -> Solution:
    return services.create_optimal_plan_unauthorized(table, mode)


@router.post('/save_solution/{table_id}', status_code=status.HTTP_201_CREATED)
def save_solution(table_id: int, solution:Solution, user_id: int, db: Session = Depends(get_db)) -> int:
    return services.save_solution(db, table_id, user_id, solution)


@router.get('/last_basic_plan/{table_id}', status_code=status.HTTP_200_OK)
def get_table_last_basic_plan(table_id: int, user_id: int,  db: Session = Depends(get_db)
                              ) -> Optional[dict[str, Solution | TransportTable]]:
    return services.get_table_last_plan(db, table_id, user_id, is_optimal=False)


@router.get('/last_optimal_plan/{table_id}', status_code=status.HTTP_200_OK)
def get_table_last_optimal_plan(table_id: int, user_id: int, db: Session = Depends(get_db)
                                ) -> Optional[dict[str, Solution | TransportTable]]:
    return services.get_table_last_plan(db, table_id, user_id, is_optimal=True)


@router.post('/register', status_code=status.HTTP_201_CREATED)
def user_register(user: User, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        user_id = services.user_register(db, user)
        return JSONResponse(
            {'message': 'success', 'user_id': user_id},
            status_code=status.HTTP_200_OK
        )
    except IntegrityError:
        return JSONResponse(
            {'message': 'Пользователь с таким именем уже существует'},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.post('/login', status_code=status.HTTP_201_CREATED)
def user_login(user: User, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        user_id = services.user_login(db, user)
        return JSONResponse(
            {'message': 'success', 'user_id': user_id},
            status_code=status.HTTP_200_OK
        )
    except AttributeError:
        return JSONResponse(
            {'message': 'Неверный логин или пароль'},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.post('/load_from_json', status_code=status.HTTP_200_OK)
def load_from_json(file: UploadFile) -> Optional[TransportTable]:
    return services.load_from_json(file.file.read())


@router.post('/save_to_json', status_code=status.HTTP_201_CREATED)
def save_to_json(table: TransportTable, solution: Solution):
    file_path = services.save_to_json(table, solution)
    return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type='multipart/form-data')
