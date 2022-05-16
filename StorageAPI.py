from fastapi import Depends, FastAPI, Body
from fastapi.security import HTTPBasic
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from CustomHTTPException import *

from Security.security import create_access_token, get_data_from_token
from Settings import config
from models.db import *
from models.requests_data import *

import secrets

from loguru import logger


class SAPI(FastAPI):

    def __init__(self):
        FastAPI.__init__(self)
        self.security = HTTPBasic()
        self.engine = create_engine(f'postgresql+psycopg2://{config.DB_USER}:{config.DB_PASS}'
                                    f'@{config.DB_HOST}/{config.DB_NAME}')
        self.engine.connect()
        logger.add('logs/logs.log', format="{time} {level} {message}")
        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

        self.DBSession = sessionmaker(bind=self.engine)
        self.session: Session = self.DBSession()
        self.methods_init()

    def user_auth_verify(self, credentials: AuthUserModel):
        user: User = self.session.query(User).filter_by(name=credentials.name).first()
        if user is None:
            logger.error('User does not exist')
            raise AuthException()

        correct_password = secrets.compare_digest(credentials.password, user.password)

        if not (credentials.name and correct_password):
            logger.error('Wrong pass')
            raise AuthException()

        return {'username': user.name, 'is_seller': user.is_seller, 'user_id': user.id}

    def user_reg_verify(self, credentials: RegUserModel):
        user: User = self.session.query(User).filter_by(name=credentials.name).first()
        if user is None:
            return credentials

        logger.error('User already exists')
        raise NameConflict()

    def methods_init(self):
        @self.post('/auth')
        def auth(credentials: dict = Depends(self.user_auth_verify)):

            access_token = create_access_token(credentials)
            logger.info(f'Token is created (is seller {credentials.get("is_seller")})): {access_token}')
            return {'access_token': access_token}

        @self.post('/reg')
        def reg(credentials: RegUserModel = Depends(self.user_reg_verify)):

            new_user = User(name=credentials.name, password=credentials.password, is_seller=credentials.is_seller)
            self.session.add(new_user)
            self.session.commit()
            token_data = {'username': new_user.name, 'is_seller': new_user.is_seller, 'user_id': new_user.id}
            access_token = create_access_token(token_data)
            logger.info(f'New user (is seller {new_user.is_seller})): {access_token}')
            return {'access_token': access_token}

        @self.post('/add_to_store')
        def add_product_to_store(access_token: str = Body(...), lable: str = '', price: float = 0, count: int = 0):
            decode_data = get_data_from_token(access_token)

            if not decode_data.get('is_seller'):
                logger.error('Forbidden exception. Not for customers')
                raise ForbiddenException()

            exists_product: Product = self.session.query(Product).filter_by(lable=lable).first()

            if exists_product is None:
                new_product = Product(lable=lable, price=price, count=count)
                self.session.add(new_product)
                self.session.commit()
                logger.info(f'Added new product: {lable}')
                return {'Product': lable}

            exists_product.count += count
            self.session.add(exists_product)
            self.session.commit()
            logger.info(f'Added {count} to exists product {lable}')
            return {'Product': lable}

        @self.post('/add_to_cart')
        def add_product_to_cart(access_token: str = Body(...), lable: str = '', count: int = 1):
            decode_data = get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                logger.error('Forbidden exception. Not for sellers')
                raise ForbiddenException()

            product: Product = self.session.query(Product).filter_by(lable=lable).first()

            if product is None:
                logger.error('Product does not exist')
                raise BadRequest()

            if product.count == 0 or product.count - count < 0:
                logger.error('Not enough count of product')
                raise LimitException()

            product.count -= count

            order: Order = self.session.query(Order).filter_by(customer_id=decode_data.get('user_id')).filter_by(
                product_id=product.id).first()

            if order is None or not order.is_active:
                order = Order(customer_id=decode_data.get('user_id'), product_id=product.id, count=0)
                logger.info('New order is created')

            order.count += count
            self.session.add(product)
            self.session.add(order)
            self.session.commit()
            logger.info('Order is updated')
            return {'Order_id': order.id}

        @self.post('/buy')
        def buy(access_token: str = Body(...)):
            decode_data = get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                logger.error('Forbidden exception. Not for sellers')
                raise ForbiddenException()

            current_orders: [Order] = self.session.query(Order) \
                .filter_by(customer_id=decode_data.get('user_id')) \
                .filter_by(is_active=True).all()

            if not current_orders:
                logger.error('Orders does not exist')
                raise BadRequest()

            total_sum = 0
            for order in current_orders:
                order.is_active = False
                self.session.add(order)
                total_sum += order.count * float(self.session.query(Product)
                                                 .filter_by(id=order.product_id)
                                                 .first().price
                                                 )
            self.session.commit()
            logger.info(f'User paid for the order: {total_sum}')
            return {'total sum': total_sum}
