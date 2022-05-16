from StorageAPI import SAPI
import requests


lable = 'testlable'
price = 123
count = 1
seller = {'name': 'seller', 'password': 'qwe'}
customer = {'name': 'user', 'password': 'qwe'}

host = 'http://127.0.0.1:8000'

old_user = {'name': 'seller', 'password': 'qwe', 'is_seller': True}
new_user = {'name': 'newuser2', 'password': 'qwe', 'is_seller': True}  # need to change username for new tests


def auth_test(data):
    response = requests.post(f'{host}/auth', json=data)
    return response.json()['access_token'], response.status_code


def test_reg_old_user():
    response = requests.post(f'{host}/reg', json=old_user)
    assert response.status_code == 409


def test_reg_new_user():
    response = requests.post(f'{host}/reg', json=new_user)
    assert response.status_code == 200


def test_add_to_store():
    access_token, status = auth_test(seller)
    assert status == 200

    response = requests.post(f'{host}/add_to_store?lable={lable}&price={price}&count={count}', json=access_token)
    assert response.status_code == 200
    assert response.json() == {'Product': lable}


def test_add_to_cart_by_seller():
    access_token, status = auth_test(seller)
    assert status == 200
    response = requests.post(f'{host}/add_to_cart?lable={lable}&count={count}', json=access_token)
    assert response.status_code == 403


def test_buy_by_seller():
    access_token, status = auth_test(seller)
    assert status == 200
    response = requests.post(f'{host}/buy', json=access_token)
    assert response.status_code == 403


def test_add_to_store_by_customer():
    access_token, status = auth_test(customer)
    assert status == 200

    response = requests.post(f'{host}/add_to_store?lable={lable}&price={price}&count={count}', json=access_token)
    assert response.status_code == 403


def test_add_to_cart():
    access_token, status = auth_test(customer)
    assert status == 200
    response = requests.post(f'{host}/add_to_cart?lable={lable}&count={count}', json=access_token)
    assert response.status_code == 200


def test_buy():
    access_token, status = auth_test(customer)
    assert status == 200
    response = requests.post(f'{host}/buy', json=access_token)
    assert response.status_code == 200
    assert response.json() == {'total sum': price * count}
