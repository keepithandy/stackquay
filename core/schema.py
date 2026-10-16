from drf_spectacular.extensions import OpenApiAuthenticationExtension


class BearerScheme(OpenApiAuthenticationExtension):
    target_class = "core.authentication.BearerAuthentication"
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "opaque"}
