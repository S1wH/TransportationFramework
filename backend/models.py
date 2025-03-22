from typing import Optional, Set
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from backend.database import Base


class Root(Base):
    __tablename__ = 'roots'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    capacity: Mapped[Optional[int]] = mapped_column()
    restriction: Mapped[Optional[str]] = mapped_column()
    price: Mapped[int] = mapped_column()

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

    transport_table_id: Mapped[int] = mapped_column(ForeignKey('transport_tables.id'), nullable=False)
    transport_table: Mapped['TransportTable'] = relationship(back_populates='roots')

    solution_roots: Mapped[Set['SolutionRoot']] = relationship(back_populates='root')

    __table_args__ = (
        CheckConstraint('supplier_id != consumer_id', name='check_supplier_consumer_different'),
    )


class Participant(Base):
    __tablename__ = 'participants'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    line_id: Mapped[int] = mapped_column()
    goods_amount: Mapped[float] = mapped_column()
    epsilon: Mapped[int] = mapped_column()
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
    roots: Mapped[Set['Root']] = relationship(back_populates='transport_table')
    solutions: Mapped[Set['TableSolution']] = relationship(back_populates='transport_table')


class SolutionRoot(Base):
    __tablename__ = 'solution_roots'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    amount: Mapped[float] = mapped_column()
    epsilon: Mapped[Optional[int]] = mapped_column(default=0, nullable=True)

    solution_id: Mapped[int] = mapped_column(ForeignKey('solutions.id'))
    solution: Mapped['TableSolution'] = relationship(back_populates='roots')

    root_id: Mapped[int] = mapped_column(ForeignKey('roots.id'))
    root: Mapped['Root'] = relationship(back_populates='solution_roots')


class TableSolution(Base):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    is_optimal: Mapped[bool] = mapped_column()
    price: Mapped[float] = mapped_column()

    table_id: Mapped[int] = mapped_column(ForeignKey('transport_tables.id'))
    transport_table: Mapped['TransportTable'] = relationship(back_populates='solutions')

    roots: Mapped[Set['SolutionRoot']] = relationship(back_populates='solution')
