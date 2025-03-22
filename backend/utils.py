import numpy as np
from backend import models
from backend.transportation_lib.transport_table import TransportTable
from sqlalchemy.orm import Session


def get_transport_table_info(db: Session, table: models.TransportTable) -> TransportTable:
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
