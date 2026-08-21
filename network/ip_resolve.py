"""

Returning ip | None, logs

info = {
    "success": False,
    "elapsed_ms": -1.0,
    "error_type": "",
    "explanation": "",
    "recommendation": "",
}

"""

import time
import socket



def dns_resolve(domain: str):
    info = {
        "success": False,
        "elapsed_ms": -1.0,
        "error_type": "",
        "explanation": "",
        "recommendation": "",
    }

    ip = None
    start = time.perf_counter()

    # Проверяем входные данные до DNS-запроса
    if not isinstance(domain, str):
        info.update(
            error_type="InvalidInput",
            explanation="Домен должен быть строкой.",
            recommendation="Передайте доменное имя в формате 'example.com'.",
        )
        return None, info

    domain = domain.strip()

    if not domain:
        info.update(
            error_type="InvalidInput",
            explanation="Доменное имя пустое.",
            recommendation="Укажите доменное имя, например 'example.com'.",
        )
        return None, info

    try:
        # Реальный DNS-запрос
        ip = socket.gethostbyname(domain)

        info.update(
            success=True,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="",
            explanation=f"Домен '{domain}' успешно разрешён в IP-адрес {ip}.",
            recommendation="Ошибок не обнаружено.",
        )

    except socket.gaierror as e:
        elapsed_ms = (time.perf_counter() - start) * 1000

        error_code = e.errno

        info["elapsed_ms"] = elapsed_ms

        if error_code == socket.EAI_NONAME:
            info.update(
                error_type="EAI_NONAME",
                explanation=(
                    f"DNS не смог найти домен '{domain}'. "
                    "Сервер имён сообщает, что такое имя не существует "
                    "или для него отсутствует подходящая DNS-запись."
                ),
                recommendation=(
                    "Проверьте правильность написания домена. "
                    "Если домен правильный, проверьте DNS-записи "
                    "и используемый DNS-сервер."
                ),
            )

        elif error_code == socket.EAI_AGAIN:
            info.update(
                error_type="EAI_AGAIN",
                explanation=(
                    "DNS-запрос временно не удалось выполнить. "
                    "Это может быть кратковременная проблема DNS-сервера "
                    "или сети."
                ),
                recommendation=(
                    "Повторите запрос через несколько секунд "
                    "и проверьте сетевое соединение."
                ),
            )

        elif error_code == socket.EAI_FAIL:
            info.update(
                error_type="EAI_FAIL",
                explanation=(
                    "DNS-сервер сообщил о постоянной ошибке "
                    "при попытке разрешить доменное имя."
                ),
                recommendation=(
                    "Проверьте доступность DNS-сервера, DNS-зону "
                    "домена и настройки сети."
                ),
            )

        elif hasattr(socket, "EAI_FAMILY") and error_code == socket.EAI_FAMILY:
            info.update(
                error_type="EAI_FAMILY",
                explanation=(
                    "DNS-запрос использовал неподдерживаемое "
                    "семейство адресов."
                ),
                recommendation=(
                    "Проверьте настройки IPv4/IPv6 "
                    "и параметры DNS-запроса."
                ),
            )

        else:
            info.update(
                error_type=f"DNS_ERROR_{error_code}",
                explanation=(
                    f"Произошла DNS-ошибка при разрешении '{domain}'. "
                    f"Системный код ошибки: {error_code}. "
                    f"Сообщение ОС: {e}"
                ),
                recommendation=(
                    "Проверьте подключение к сети, настройки DNS "
                    "и доступность DNS-сервера."
                ),
            )

    except socket.timeout:
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="Timeout",
            explanation=(
                f"DNS-запрос для '{domain}' превысил допустимое "
                "время ожидания."
            ),
            recommendation=(
                "Проверьте соединение с интернетом и доступность "
                "DNS-сервера. Попробуйте другой DNS-сервер."
            ),
        )

    except OSError as e:
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="OSError",
            explanation=(
                "Операционная система не смогла выполнить DNS-запрос. "
                f"Сообщение ОС: {e}"
            ),
            recommendation=(
                "Проверьте сетевое подключение, настройки DNS "
                "и системные сетевые параметры."
            ),
        )

    except Exception as e:
        # Последний защитный слой:
        # функция не должна неожиданно уронить программу.
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type=type(e).__name__,
            explanation=(
                "Произошла непредвиденная ошибка во время "
                f"DNS-разрешения: {e}"
            ),
            recommendation=(
                "Проверьте входные данные и состояние системы. "
                "Если ошибка повторяется, сохраните её тип и сообщение "
                "для дальнейшей диагностики."
            ),
        )

    return ip, info