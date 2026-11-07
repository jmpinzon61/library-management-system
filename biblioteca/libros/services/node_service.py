import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NodeServiceError(Exception):
    pass


def _request(path, payload=None):
    base_url = os.getenv("NODE_SERVICE_URL", "").rstrip("/")
    token = os.getenv("NODE_SERVICE_TOKEN", "")
    if not base_url or not token:
        raise NodeServiceError(
            "Configura NODE_SERVICE_URL y NODE_SERVICE_TOKEN."
        )

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=data,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            **({"Content-Type": "application/json"} if data else {}),
        },
        method="GET" if data is None else "POST",
    )

    try:
        with urlopen(request, timeout=55) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 401:
            message = "El microservicio rechazó las credenciales de servicio."
        elif error.code == 503:
            message = "El microservicio o la integración de IA no está disponible."
        else:
            message = f"El microservicio respondió con HTTP {error.code}."
        raise NodeServiceError(message) from error
    except (TimeoutError, URLError) as error:
        raise NodeServiceError(
            "No fue posible comunicarse con el microservicio Node.js."
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NodeServiceError(
            "El microservicio devolvió una respuesta inválida."
        ) from error

    if not isinstance(result, dict):
        raise NodeServiceError("El microservicio devolvió una respuesta inválida.")
    return result


def get_overdue_notifications():
    result = _request("/api/notifications/overdue")
    notifications = result.get("notifications")
    if not isinstance(notifications, list):
        raise NodeServiceError("La respuesta de alertas no tiene el formato esperado.")
    return notifications


def sync_overdue_notifications(loans):
    return _request(
        "/api/notifications/overdue/sync",
        {"loans": loans},
    )


def generate_recommendations(question, catalog):
    result = _request(
        "/api/ai/recommendations",
        {"question": question, "catalog": catalog},
    )
    answer = result.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise NodeServiceError("La respuesta de recomendaciones está vacía.")
    return answer


def generate_book_summary(book):
    result = _request("/api/ai/summaries", {"book": book})
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise NodeServiceError("La respuesta del resumen está vacía.")
    return summary
