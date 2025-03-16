from sqlalchemy.orm import Session
from backend import models, schemas
from backend.transportation_lib import transport_table


def get_tables(db: Session):
    tables = db.query(models.TransportTable).all()
    return tables


def create_table(table: schemas.TransportTable, db: Session):
    with db as session:
        t1 = transport_table.TransportTable(**table)
        t1.pprint()
        # table = models.TransportTable()
        # session.add(table)
        # session.commit()
        # session.refresh(table)
        # print(table.id)
