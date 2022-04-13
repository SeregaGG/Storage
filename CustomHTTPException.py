from fastapi import HTTPException, status


class HTTPExceptions:
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        # headers={"WWW-Authenticate": "Basic"},
    )

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to the requested resource is forbidden"
    )

    limit_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Not found"
    )

    bad_request = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Bad_request"
    )

    name_conflict = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="User already exists"
    )
