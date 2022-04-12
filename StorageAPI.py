from fastapi import Depends, Request, FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from CustomHTTPException import HTTPExceptions

from Settings import config, settings
from models.models import *

from jose import JWTError, jwt

import secrets
from datetime import datetime, timedelta

from loguru import logger


class SAPI(FastAPI):

    def __init__(self):
        FastAPI.__init__(self)
        self.str_format = '%d.%m.%Y %H:%M:%S'
        self.security = HTTPBasic()
        self.engine = create_engine(f'postgresql+psycopg2://{config.DB_USER}:{config.DB_PASS}'
                                    f'@{config.DB_HOST}/{config.DB_NAME}')

        self.engine.connect()
        self.exceptions = HTTPExceptions()
        logger.add('logs/logs.log', format='{time} {level} {message}')
        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

        self.DBSession = sessionmaker(bind=self.engine)
        self.session: Session = self.DBSession()
        self.methods_init()

    def create_access_token(self, data: dict):
        encode_data = data.copy()
        last_moment = (datetime.utcnow() + timedelta(minutes=15)).strftime(self.str_format)
        encode_data.update({'last_moment': last_moment})
        encode_jwt = jwt.encode(encode_data, settings.SECRET_KEY, settings.ALGORITHM)
        return encode_jwt

    def get_data_from_token(self, access_token: str):
        decode_data = jwt.decode(access_token, settings.SECRET_KEY, settings.ALGORITHM)
        last_moment = datetime.strptime(decode_data.get('last_moment'), self.str_format)

        if last_moment is None:
            raise self.exceptions.auth_exception

        if datetime.utcnow() > last_moment:
            raise self.exceptions.auth_exception

        return decode_data

    def methods_init(self):
        @logger.catch
        @self.get('/auth')
        def auth(request: Request, credentials: HTTPBasicCredentials = Depends(self.security)):
            user: User = self.session.query(User).filter_by(name=credentials.username).first()
            if user is None:
                raise self.exceptions.auth_exception

            correct_password = secrets.compare_digest(credentials.password, user.password)

            if not (credentials.username and correct_password):
                raise self.exceptions.auth_exception

            user_data = {'username': credentials.username, 'is_seller': user.is_seller, 'user_id': user.id}
            access_token = self.create_access_token(user_data)
            return {'access_token': access_token}

        @logger.catch
        @self.post('/add_to_store')
        def add_product_to_store(access_token: str, lable: str, price: float, count: int = 0):
            decode_data = self.get_data_from_token(access_token)

            if not decode_data.get('is_seller'):
                raise self.exceptions.forbidden_exception

            exists_product: Product = self.session.query(Product).filter_by(lable=lable).first()

            if exists_product is None:
                new_product = Product(lable=lable, price=price, count=count)
                self.session.add(new_product)
                self.session.commit()
                return {'Product': lable}

            exists_product.count += count
            self.session.add(exists_product)
            self.session.commit()
            return {'Product': lable}

        @logger.catch
        @self.post('/add_to_cart')
        def add_product_to_cart(access_token: str, lable: str, count: int = 1):
            decode_data = self.get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                raise self.exceptions.forbidden_exception

            product: Product = self.session.query(Product).filter_by(lable=lable).first()

            if product is None:
                raise self.exceptions.bad_request

            if product.count == 0 or product.count - count < 0:
                raise self.exceptions.limit_exception

            product.count -= count

            order: Order = self.session.query(Order).filter_by(customer_id=decode_data.get('user_id')).filter_by(
                product_id=product.id).first()

            if order is None or not order.is_active:
                order = Order(customer_id=decode_data.get('user_id'), product_id=product.id, count=0)

            order.count += count
            self.session.add(product)
            self.session.add(order)
            self.session.commit()
            return {'Order_id': order.id}

        @logger.catch
        @self.post('/buy')
        def buy(access_token: str):
            decode_data = self.get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                raise self.exceptions.forbidden_exception

            current_orders: [Order] = self.session.query(Order) \
                .filter_by(customer_id=decode_data.get('user_id')) \
                .filter_by(is_active=True).all()

            if not current_orders:
                raise self.exceptions.bad_request

            total_sum = 0
            for order in current_orders:
                order.is_active = False
                self.session.add(order)
                total_sum += order.count * float(self.session.query(Product)
                                                 .filter_by(id=order.product_id)
                                                 .first().price
                                                 )
            self.session.commit()
            return {'total sum': total_sum}
