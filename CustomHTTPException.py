from fastapi import HTTPException, status


class AuthException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Incorrect username or password")


class ForbiddenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN,
                         detail="Access to the requested resource is forbidden")


class LimitException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Not found")


class BadRequest(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST,
                         detail="Bad_request")


class NameConflict(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT,
                         detail="User already exists")
