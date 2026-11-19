class AuthError(Exception):
    """Base class for authentication/user service errors."""


class InvalidEmailError(AuthError):
    pass


class WeakPasswordError(AuthError):
    pass


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass
