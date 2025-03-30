from typing import Optional
from sqlalchemy import ColumnElement
from sqlalchemy.orm import Session
from backend import models, schemas, utils


def get_tables(db: Session) -> list[schemas.TransportTable]:
    tables = []
    for table_id in db.query(models.TransportTable.id).distinct():
        table_schema = get_table(db, table_id[0])
        tables.append(table_schema)
    return tables


def get_table(db: Session, table_id: int | ColumnElement[int]) -> Optional[schemas.TransportTable]:
    with db as session:
        table = session.get(models.TransportTable, table_id)
        suppliers = session.query(models.Participant).filter_by(
            transport_table_id=table_id, is_supplier=True).order_by('line_id')
        consumers = session.query(models.Participant).filter_by(
            transport_table_id=table_id, is_supplier=False).order_by('line_id')
        roots = table.roots
        price_matrix = [[0 for _ in range(consumers.count())] for _ in range(suppliers.count())]
        capacities = [[0 for _ in range(consumers.count())] for _ in range(suppliers.count())
                      ] if list(roots)[0].capacity else []
        restrictions = {}
        for root in roots:
            supplier_id = root.supplier.line_id
            consumer_id = root.consumer.line_id
            price_matrix[supplier_id][consumer_id] = root.price

            if root.restriction:
                restrictions[f'{supplier_id}, {consumer_id}'] = root.restriction

            if root.capacity:
                capacities[supplier_id][consumer_id] = root.capacity
        table_scheme = schemas.TransportTable(
            suppliers=[supplier.goods_amount for supplier in suppliers],
            consumers=[consumer.goods_amount for consumer in consumers],
            price_matrix=price_matrix,
            restrictions=restrictions,
            capacities=capacities,
        )
    return table_scheme


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
                restriction_key = f'{row_idx}, {col_idx}'
                session_root = models.Root(
                    capacity=table.capacities[row_idx][col_idx] if table.capacities else None,
                    restriction=table.restrictions[restriction_key]
                                if table.restrictions and restriction_key in table.restrictions.keys() else None,
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

    roots, price = t.create_basic_plan(mode)
    return schemas.Solution(price=price, is_optimal=False, roots=roots)


def create_optimal_plan(db: Session, table_id: int, mode: int) -> schemas.Solution:
    table = db.get(models.TransportTable, table_id)

    t = utils.get_transport_table_info(db, table)
    if t.has_capacities:
        roots, price = t.solve_capacity_plan()
    else:
        t.create_basic_plan(mode)
        roots, price = t.create_optimal_plan()
    return schemas.Solution(price=price, is_optimal=True, roots=roots)


def save_solution(db: Session, table_id: int, table_solution: schemas.Solution) -> int:
    with db as session:
        solution = models.TableSolution(
            is_optimal=table_solution.is_optimal,
            price=table_solution.price,
            table_id=table_id
        )
        session.add(solution)
        session.commit()
        session.refresh(solution)

        solution_roots = []
        for root in table_solution.roots:
            supplier_id = session.query(models.Participant).filter_by(
                transport_table_id=table_id,
                line_id=root['supplier_id'],
                is_supplier=True,
            ).one().id
            consumer_id = session.query(models.Participant).filter_by(
                transport_table_id=table_id,
                line_id=root['consumer_id'],
                is_supplier=False,
            ).one().id

            base_root = session.query(models.Root).filter_by(
                supplier_id=supplier_id,
                consumer_id=consumer_id,
                transport_table_id=table_id
            ).one()

            solution_root = models.SolutionRoot(
                amount=root['amount'],
                epsilon=root['epsilon'],
                solution_id=solution.id,
                root=base_root,
            )
            solution_roots.append(solution_root)

        session.add_all(solution_roots)
        session.commit()
        return solution.id


def get_table_last_plan(db: Session, table_id: int, is_optimal: bool) -> Optional[schemas.Solution]:
    with db as session:
        last_plan = session.query(models.TableSolution).filter_by(
            table_id=table_id, is_optimal=is_optimal
        ).order_by(models.TableSolution.id.desc()).first()

        if not last_plan:
            return None

        last_plan = schemas.Solution(
            price=last_plan.price,
            is_optimal=last_plan.is_optimal,
            roots=utils.get_root_info(last_plan.roots),
        )
    return last_plan
