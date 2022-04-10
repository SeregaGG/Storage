import sqlalchemy.orm
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from CustomHTTPException import HTTPExceptions


from Settings import config, settings
from models.models import *

from jose import JWTError, jwt


import secrets
from datetime import datetime, timedelta


class SAPI(FastAPI):

    def __init__(self):
        FastAPI.__init__(self)
        self.str_format = '%d.%m.%Y %H:%M:%S'
        self.security = HTTPBasic()
        self.engine = create_engine('postgresql+psycopg2://postgres:9fbj5kn@localhost/storage')
        self.engine.connect()
        self.exceptions = HTTPExceptions()

        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

        self.DBSession = sessionmaker(bind=self.engine)
        self.session: sqlalchemy.orm.Session = self.DBSession()
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
        @self.get('/auth')
        def auth(credentials: HTTPBasicCredentials = Depends(self.security)):
            user: User = self.session.query(User).filter_by(name=credentials.username).first()

            if user is None:
                raise self.exceptions.auth_exception

            correct_password = secrets.compare_digest(credentials.password, user.password)

            if not (credentials.username and correct_password):
                raise self.exceptions.auth_exception

            user_data = {'username': credentials.username, 'is_seller': user.is_seller, 'user_id': user.id}
            access_token = self.create_access_token(user_data)
            return access_token

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
                return {'New product': lable}

            exists_product.count += count
            self.session.add(exists_product)
            self.session.commit()
            return {'Product': lable}

        @self.post('/add_to_cart')
        def add_product_to_cart(access_token: str, lable: str, count: int = 1):
            decode_data = self.get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                raise self.exceptions.forbidden_exception

            product: Product = self.session.query(Product).filter_by(lable=lable).first()

            if product is None:
                raise self.exceptions.bad_request

            if product.count == 0:
                raise self.exceptions.limit_exception

            orders: [Order] = self.session.query(Order).filter_by(customer_id=decode_data.get('user_id')).all()

            for order in orders:
                if product.count - count < 0:
                    raise self.exceptions.limit_exception

                if product.id == order.product_id and order.is_active:
                    order.count += count
                    product.count -= count
                    self.session.add(product)
                    self.session.add(order)
                    self.session.commit()
                    return {'Order_id': order.id}

            new_order = Order(customer_id=decode_data.get('user_id'), product_id=product.id, count=count)

            if product.count - count < 0:
                raise self.exceptions.limit_exception
            product.count -= count
            self.session.add(product)
            self.session.add(new_order)
            self.session.commit()
            return {'New_order_id': new_order.id}

        @self.post('/buy')
        def buy(access_token: str):
            decode_data = self.get_data_from_token(access_token)

            if decode_data.get('is_seller'):
                raise self.exceptions.forbidden_exception

            current_orders: [Order] = self.session.query(Order).filter_by(customer_id=decode_data.get('user_id')).all()

            if not current_orders:
                raise self.exceptions.bad_request

            total_sum = 0
            for order in current_orders:
                if order.is_active:
                    order.is_active = False
                    self.session.add(order)
                    total_sum += order.count * float(self.session.query(Product).filter_by(id=order.product_id).first().price)
            self.session.commit()
            return {'total sum': total_sum}