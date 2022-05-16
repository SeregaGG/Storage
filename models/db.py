from sqlalchemy import Column, ForeignKey, Integer, String, MetaData, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    is_seller = Column(Boolean, default=False)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, nullable=False)
    count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    lable = Column(String(250), nullable=False)
    price = Column(String(250), nullable=False)
    count = Column(Integer, default=0)
