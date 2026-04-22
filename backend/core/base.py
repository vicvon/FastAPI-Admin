from sqlmodel import SQLModel


class Base(SQLModel):
    __abstract__ = True
