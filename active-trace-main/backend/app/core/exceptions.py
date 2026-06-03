"""
Custom domain exceptions for Clean Architecture HTTP error mapping.
"""


class ServiceError(Exception):
    """Domain/service-level error. Routers map this to HTTP 422 (or 409 for state conflicts)."""
