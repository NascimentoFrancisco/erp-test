import logging
import time
import uuid

from apps.core.observability import reset_correlation_id, set_correlation_id


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("api.request")

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        token = set_correlation_id(correlation_id)

        request.correlation_id = correlation_id
        start = time.perf_counter()
        client_ip = self._get_client_ip(request)

        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self.logger.exception(
                "Unhandled exception during request",
                extra={
                    "request_method": request.method,
                    "request_path": request.get_full_path(),
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code
            level = logging.INFO
            if status_code >= 500:
                level = logging.ERROR
            elif status_code >= 400:
                level = logging.WARNING

            self.logger.log(
                level,
                "HTTP request completed",
                extra={
                    "request_method": request.method,
                    "request_path": request.get_full_path(),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            response["X-Correlation-ID"] = correlation_id
            return response
        finally:
            reset_correlation_id(token)

    def _get_client_ip(self, request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "-")
