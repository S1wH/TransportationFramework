import numpy as np
from typing import Optional, List, Type
from sqlalchemy.orm import Session
from backend import models, schemas, utils


def get_tables(db: Session) -> List[Type[schemas.TransportTable]]:
    tables = db.query(models.TransportTable).all()
    return tables


def get_table(db: Session, table_id: int) -> Optional[Type[schemas.TransportTable]]:
    table = db.get(models.TransportTable, table_id)
    return table


def create_table(db: Session, table: schemas.TransportTable) -> int:
    with db as session:
        t_table = models.TransportTable()
        session.add(t_table)
        session.commit()
        session.refresh(t_table)

        suppliers = []
        for idx, supplier in enumerate(table.suppliers):
            session_supplier = models.Participant(
                line_id=idx,
                goods_amount=supplier,
                epsilon=0,
                is_supplier=True,
                transport_table_id=t_table.id,
            )
            suppliers.append(session_supplier)
        session.add_all(suppliers)
        session.commit()
        for supplier in suppliers:
            session.refresh(supplier)

        consumers = []
        for idx, consumer in enumerate(table.consumers):
            session_consumer = models.Participant(
                line_id=idx,
                goods_amount=consumer,
                epsilon=0,
                is_supplier=False,
                transport_table_id=t_table.id,
            )
            consumers.append(session_consumer)
        session.add_all(consumers)
        session.commit()
        for consumer in consumers:
            session.refresh(consumer)

        roots = []
        for row_idx, row in enumerate(table.price_matrix):
            for col_idx, item in enumerate(row):
                session_root = models.Root(
                    capacity=table.capacities[row_idx][col_idx] if table.capacities else None,
                    restriction=table.restrictions[(row_idx, col_idx)][0] +
                                str(table.restrictions[(row_idx, col_idx)][1])
                                if (row_idx, col_idx) in table.restrictions.keys() else None,
                    price=item,
                    supplier_id=suppliers[row_idx].id,
                    consumer_id=consumers[col_idx].id,
                    transport_table_id=t_table.id,
                )
                roots.append(session_root)
        session.add_all(roots)
        session.commit()

        return t_table.id


def create_basic_plan(db: Session, table_id: int, mode: int) -> schemas.Solution:
    table = db.get(models.TransportTable, table_id)

    t = utils.get_transport_table_info(db, table)

    solution, price = t.create_basic_plan(mode)
    return schemas.Solution(price=price, transition_matrix=solution, is_optimal=False)


def create_optimal_plan(db: Session, table_id: int, mode: int) -> schemas.Solution:
    table = db.get(models.TransportTable, table_id)

    t = utils.get_transport_table_info(db, table)
    if t.has_capacities:
        solution, price = t.solve_capacity_plan()
    else:
        t.create_basic_plan(mode)
        solution, price = t.create_optimal_plan()
    return schemas.Solution(price=price, transition_matrix=solution, is_optimal=True)
