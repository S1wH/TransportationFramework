from typing import Optional
from sqlalchemy import ColumnElement
from sqlalchemy.orm import Session, Mapped
from backend import models, schemas, utils


def get_tables(db: Session, user_id: int) -> list[schemas.TransportTable]:
    tables = []
    for table_id in db.query(models.TransportTable.id).distinct():
        table_schema = get_table(db, table_id[0], user_id, is_dummy=False)
        tables.append(table_schema)
    return tables


def get_table(db: Session, table_id: int | ColumnElement[int], user_id: int, is_dummy: Optional[bool]=False
              ) -> Optional[schemas.TransportTable]:
    with db as session:
        table = session.get(models.TransportTable, table_id)
        suppliers = session.query(models.Participant.id, models.Participant.goods_amount).filter_by(
            transport_table_id=table_id, is_supplier=True)
        consumers = session.query(models.Participant.id, models.Participant.goods_amount).filter_by(
            transport_table_id=table_id, is_supplier=False)

        if is_dummy is not None:
            suppliers = suppliers.filter_by(is_dummy=is_dummy).order_by('line_id')
            consumers = consumers.filter_by(is_dummy=is_dummy).order_by('line_id')
        roots = session.query(models.Root).filter_by(transport_table_id=table_id).filter(
            models.Root.supplier_id.in_([s[0] for s in suppliers]),
            models.Root.consumer_id.in_([c[0] for c in consumers])
        )
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
            id=table.id,
            name=table.name,
            suppliers=[s[1] for s in suppliers],
            consumers=[c[1] for c in consumers],
            price_matrix=price_matrix,
            restrictions=restrictions,
            capacities=capacities,
            user_id=user_id,
        )
    return table_scheme


def create_table(db: Session, table: schemas.TransportTable) -> int:
    with db as session:
        user = session.get(models.User, table.user_id)

        t_table = models.TransportTable(user_id=user.id, name=table.name)
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
                restriction_key = f'{row_idx},{col_idx}'
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
    return schemas.Solution(
        price=price,
        is_optimal=False,
        roots=roots,
        suppliers=t.amount_suppliers,
        consumers=t.amount_consumers
    )


def create_basic_plan_unauthorized(table: schemas.TransportTable, mode: int) -> schemas.Solution:
    t = utils.get_transport_table_info_unauthorized(table)
    roots, price = t.create_basic_plan(mode)
    return schemas.Solution(
        price=price,
        is_optimal=False,
        roots=roots,
        suppliers=t.amount_suppliers,
        consumers=t.amount_consumers
    )


def create_optimal_plan(db: Session, table_id: int, mode: int) -> schemas.Solution:
    table = db.get(models.TransportTable, table_id)

    t = utils.get_transport_table_info(db, table)
    if t.has_capacities:
        roots, price = t.solve_capacity_plan()
    else:
        t.create_basic_plan(mode)
        roots, price = t.create_optimal_plan()
    return schemas.Solution(
        price=price,
        is_optimal=True,
        roots=roots,
        suppliers=t.amount_suppliers,
        consumers=t.amount_consumers
    )


def create_optimal_plan_unauthorized(table: schemas.TransportTable, mode: int) -> schemas.Solution:
    t = utils.get_transport_table_info_unauthorized(table)
    if t.has_capacities:
        roots, price = t.solve_capacity_plan()
    else:
        t.create_basic_plan(mode)
        roots, price = t.create_optimal_plan()
    return schemas.Solution(
        price=price,
        is_optimal=True,
        roots=roots,
        suppliers=t.amount_suppliers,
        consumers=t.amount_consumers
    )


def save_solution(db: Session, table_id: int, user_id: int, table_solution: schemas.Solution) -> Optional[int]:
    with db as session:
        if not session.get(models.User, user_id):
            return None

        solution = models.TableSolution(
            is_optimal=table_solution.is_optimal,
            price=table_solution.price,
            table_id=table_id,
            amount_suppliers=table_solution.suppliers,
            amount_consumers=table_solution.consumers,
        )
        session.add(solution)
        session.commit()
        session.refresh(solution)

        solution_roots = []
        for root in table_solution.roots:
            supplier_query = session.query(models.Participant).filter_by(
                transport_table_id=table_id,
                line_id=root['supplier_id'],
                is_supplier=True,
            )
            consumer_query = session.query(models.Participant).filter_by(
                transport_table_id=table_id,
                line_id=root['consumer_id'],
                is_supplier=False,
            )
            if supplier_query.count() == 0:
                supplier = models.Participant(
                    line_id=root['supplier_id'],
                    goods_amount=root['amount'],
                    epsilon=root['epsilon'],
                    is_supplier=True,
                    is_dummy=True,
                    transport_table_id=table_id,
                )
                session.add(supplier)
                session.commit()
                session.refresh(supplier)
                supplier_id = supplier.id

                roots = []
                for c_id in session.query(models.Participant.id).filter_by(transport_table_id=table_id,
                                                                              is_supplier=False).distinct():
                    session_root = models.Root(
                        capacity=0,
                        restriction=None,
                        price=0,
                        supplier_id=supplier_id,
                        consumer_id=c_id[0],
                        transport_table_id=table_id,
                    )
                    roots.append(session_root)
                session.add_all(roots)
                session.commit()

            else:
                supplier_id = supplier_query.one().id

            if consumer_query.count() == 0:
                consumer = models.Participant(
                    line_id=root['consumer_id'],
                    goods_amount=root['amount'],
                    epsilon=root['epsilon'],
                    is_supplier=False,
                    is_dummy=True,
                    transport_table_id=table_id,
                )
                session.add(consumer)
                session.commit()
                session.refresh(consumer)
                consumer_id = consumer.id

                roots = []
                for s_id in session.query(models.Participant.id).filter_by(transport_table_id=table_id,
                                                                              is_supplier=True).distinct():
                    session_root = models.Root(
                        capacity=0,
                        restriction=None,
                        price=0,
                        supplier_id=s_id[0],
                        consumer_id=consumer_id,
                        transport_table_id=table_id,
                    )
                    roots.append(session_root)
                session.add_all(roots)
                session.commit()

            else:
                consumer_id = consumer_query.one().id

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


def get_table_last_plan(db: Session, table_id: int, user_id: int, is_optimal: bool
                        ) -> Optional[dict[str, schemas.Solution | schemas.TransportTable]]:
    with db as session:
        table_schema = get_table(db, table_id, user_id, is_dummy=None)

        last_plan = session.query(models.TableSolution).filter_by(
            table_id=table_id, is_optimal=is_optimal
        ).order_by(models.TableSolution.id.desc()).first()

        if not last_plan:
            return None

        last_plan = schemas.Solution(
            price=last_plan.price,
            is_optimal=last_plan.is_optimal,
            roots=utils.get_root_info(last_plan.roots),
            suppliers=last_plan.amount_suppliers,
            consumers=last_plan.amount_consumers
        )

        output_data = {
            'table': table_schema,
            'solution': last_plan
        }
        return output_data


def user_register(db: Session, user: schemas.User) -> int:
    with db as session:
        password_hash = utils.get_password_hash(user.password)
        user_model = models.User(
            username=user.username,
            password=password_hash,
        )
        session.add(user_model)
        session.commit()
        session.refresh(user_model)
        return user_model.id


def user_login(db: Session, user: schemas.User) -> int | Mapped[int]:
    with db as session:
        password_to_verify = utils.get_password_hash(user.password)
        user = session.query(models.User).filter_by(username=user.username, password=password_to_verify).first()
        return user.id
