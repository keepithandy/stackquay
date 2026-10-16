from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        request = context.get("request")
        response.data = {
            "error": {"status": response.status_code, "details": response.data},
            "request_id": getattr(request, "request_id", None),
        }
    return response
