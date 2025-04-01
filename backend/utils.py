from typing import Type
from sqlalchemy.orm import Session
import numpy as np
from backend import models, schemas
from backend.models import SolutionRoot
from backend.transportation_lib.transport_table import TransportTable


def get_transport_table_info(db: Session, table: Type[models.TransportTable]) -> TransportTable:
    with db as session:
        consumers = [p.goods_amount for p in session.query(models.Participant)
        .filter_by(transport_table_id=table.id, is_supplier=False)
        .order_by(models.Participant.line_id)]

        suppliers = [p.goods_amount for p in session.query(models.Participant)
        .filter_by(transport_table_id=table.id, is_supplier=True)
        .order_by(models.Participant.line_id)]

        price_matrix = np.zeros((len(suppliers), len(consumers)), dtype=np.float16)
        capacities = np.zeros((len(suppliers), len(consumers)), dtype=np.float16) \
            if list(table.roots)[0].capacity else None

        restrictions = {}
        for root in table.roots:
            supplier_id = root.supplier.line_id
            consumer_id = root.consumer.line_id
            price_matrix[supplier_id][consumer_id] = root.price
            if root.capacity:
                capacities[supplier_id][consumer_id] = root.capacity

            restriction = root.restriction
            if restriction:
                restrictions[(supplier_id, consumer_id)] = (restriction[0], int(restriction[1:]))

    return TransportTable(list(suppliers), list(consumers), price_matrix, restrictions, capacities)


def get_transport_table_info_unauthorized(table: schemas.TransportTable) -> TransportTable:
    restrictions = {}
    if table.restrictions:
        for k, v in table.restrictions.items():
            row_id, col_id = map(int, k.split(','))
            restrictions[(row_id, col_id)] = (v[0], int(v[1::]))
    return TransportTable(table.suppliers, table.consumers, np.array(table.price_matrix, dtype=np.float16),
                          restrictions, table.capacities)


def get_root_info(roots: set[SolutionRoot]) -> list[dict[str, int | float]]:
    transition_roots = []
    for root in roots:
        base_root = root.root
        transition_root = {
            'supplier_id': base_root.supplier.line_id,
            'consumer_id': base_root.supplier.line_id,
            'amount': root.amount,
            'epsilon': root.epsilon,
        }
        transition_roots.append(transition_root)
    return transition_roots
