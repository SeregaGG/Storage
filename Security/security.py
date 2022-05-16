from datetime import datetime, timedelta
from jose import jwt
from Settings import settings
from loguru import logger
from CustomHTTPException import AuthException
str_format = '%d.%m.%Y %H:%M:%S'


def create_access_token(data: dict, tokenlifetime=15):
    encode_data = data.copy()
    last_moment = (datetime.utcnow() + timedelta(minutes=tokenlifetime)).strftime(str_format)
    encode_data.update({'last_moment': last_moment})
    encode_jwt = jwt.encode(encode_data, settings.SECRET_KEY, settings.ALGORITHM)
    return encode_jwt


def get_data_from_token(access_token: str):
    decode_data = jwt.decode(access_token, settings.SECRET_KEY, settings.ALGORITHM)
    last_moment = datetime.strptime(decode_data.get('last_moment'), str_format)

    if last_moment is None:
        logger.error('Bad token')
        raise AuthException()

    if datetime.utcnow() > last_moment:
        logger.error('Lifetime of token is ended')
        raise AuthException()

    return decode_data
