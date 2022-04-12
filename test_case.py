from StorageAPI import SAPI
from fastapi.testclient import TestClient

app = SAPI()
client = TestClient(app)
lable = 'testlable'
price = 123
count = 1
seller_hash_data = 'c2VsbGVyOnF3ZQ=='  # user: seller; password: qwe
customer_hash_data = 'dXNlcjpxd2U='  # user: user; password: qwe


def auth_test(hash_data):
    response = client.get(f'/auth', headers={'Authorization': f'Basic {hash_data}='})

    return response.json()['access_token'], response.status_code


def test_add_to_store():
    access_token, status = auth_test(seller_hash_data)
    assert status == 200

    response = client.post(f'/add_to_store?access_token={access_token}&lable={lable}&price={price}&count={count}')
    assert response.status_code == 200
    assert response.json() == {'Product': lable}


def test_add_to_cart_by_seller():
    access_token, status = auth_test(seller_hash_data)
    assert status == 200
    response = client.post(f'/add_to_cart?access_token={access_token}&lable={lable}&count={count}')
    assert response.status_code == 403


def test_buy_by_seller():
    access_token, status = auth_test(seller_hash_data)
    assert status == 200
    response = client.post(f'/buy?access_token={access_token}')
    assert response.status_code == 403


def test_add_to_store_by_customer():
    access_token, status = auth_test(customer_hash_data)
    assert status == 200

    response = client.post(f'/add_to_store?access_token={access_token}&lable={lable}&price={price}&count={count}')
    assert response.status_code == 403


def test_add_to_cart():
    access_token, status = auth_test(customer_hash_data)
    assert status == 200
    response = client.post(f'/add_to_cart?access_token={access_token}&lable={lable}&count={count}')
    assert response.status_code == 200


def test_buy():
    access_token, status = auth_test(customer_hash_data)
    assert status == 200
    response = client.post(f'/buy?access_token={access_token}')
    assert response.status_code == 200
    assert response.json() == {'total sum': price * count}
