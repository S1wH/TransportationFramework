from typing import Optional, Set
from sqlalchemy import ForeignKey, Table, Column, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from backend.database import Base


root_to_solution_table = Table(
    "root_to_solution_table",
    Base.metadata,
    Column('root_id', ForeignKey('roots.id'), primary_key=True),
    Column('solution_id', ForeignKey('solutions.id'), primary_key=True),
)


class Root(Base):
    __tablename__ = 'roots'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    capacity: Mapped[Optional[int]] = mapped_column()
    restriction: Mapped[Optional[int]] = mapped_column()
    price: Mapped[int] = mapped_column()
    epsilon: Mapped[int] = mapped_column()
    amount: Mapped[float] = mapped_column()
    repr: Mapped[str] = mapped_column(default='0')

    supplier_id: Mapped[int] = mapped_column(ForeignKey('participants.id'), nullable=False)
    supplier: Mapped['Participant'] = relationship(
        back_populates='supplier_root',
        primaryjoin='Root.supplier_id == Participant.id'
    )

    consumer_id: Mapped[int] = mapped_column(ForeignKey('participants.id'), nullable=False)
    consumer: Mapped['Participant'] = relationship(
        back_populates='consumer_root',
        primaryjoin='Root.consumer_id == Participant.id'
    )

    solutions: Mapped[Set['TableSolution']] = relationship(
        secondary=root_to_solution_table,
        back_populates='roots'
    )

    __table_args__ = (
        CheckConstraint('supplier_id != consumer_id', name='check_supplier_consumer_different'),
    )


class Participant(Base):
    __tablename__ = 'participants'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    goods_amount: Mapped[float] = mapped_column()
    real_goods_amount: Mapped[float] = mapped_column()
    epsilon: Mapped[int] = mapped_column()
    real_epsilon: Mapped[int] = mapped_column()
    is_supplier: Mapped[bool] = mapped_column(default=True)

    transport_table_id: Mapped[int] = mapped_column(ForeignKey('transport_tables.id'))
    transport_table: Mapped['TransportTable'] = relationship(back_populates='participants')

    supplier_root: Mapped[Optional['Root']] = relationship(
        back_populates='supplier',
        foreign_keys=[Root.supplier_id]
    )
    consumer_root: Mapped[Optional['Root']] = relationship(
        back_populates='consumer',
        foreign_keys=[Root.consumer_id]
    )


class TransportTable(Base):
    __tablename__ = 'transport_tables'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    participants: Mapped[Set['Participant']] = relationship(back_populates='transport_table')
    solutions: Mapped[Set['TableSolution']] = relationship(back_populates='transport_table')


class TableSolution(Base):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    is_optimal: Mapped[bool] = mapped_column()
    price: Mapped[float] = mapped_column()

    table_id: Mapped[int] = mapped_column(ForeignKey('transport_tables.id'))
    transport_table: Mapped['TransportTable'] = relationship(back_populates='solutions')

    roots: Mapped[Set['Root']] = relationship(secondary=root_to_solution_table, back_populates='solutions')
