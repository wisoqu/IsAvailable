import socket
import ssl
import time


def http_check(conn, domain: str, path: str = "/") -> tuple[dict | None, dict]:
    """Выполняет HTTP(S)-запрос поверх уже установленного соединения
    (TCP или TLS — этому слою всё равно, у обоих есть sendall/recv).

    Возвращает (response_info | None, info), где response_info — статус-код
    и заголовки, а info — контракт слоя, как у остальных проверок.
    """

    info = {
        "type": "HTTP_CHECK",
        "success": None,
        "elapsed_ms": -1.0,
        "ttfb_ms": -1.0,
        "error_type": "",
        "explanation": "",
        "recommendation": "",
    }

    start = time.perf_counter()

    # Проверяем соединение до отправки запроса —
    # тот же паттерн, что в tls_handshake для conn is None
    if conn is None:
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidConnection",
            explanation="Connection is None. HTTP request cannot be sent.",
            recommendation="Make sure the previous layer (TCP/TLS) succeeded before calling HTTP.",
        )
        return None, info

    if not isinstance(conn, (socket.socket, ssl.SSLSocket)):
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidConnection",
            explanation=f"Expected socket or SSL socket, but received {type(conn).__name__}.",
            recommendation="Pass the connection object returned by the TCP or TLS layer.",
        )
        return None, info

    if not isinstance(domain, str) or not domain.strip():
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidDomain",
            explanation="Domain must be a non-empty string.",
            recommendation="Provide the domain used for the TLS/TCP connection.",
        )
        return None, info

    domain = domain.strip()

    # Собираем сырой HTTP-запрос текстом.
    # \r\n — обязательный разделитель строк в HTTP-протоколе (не просто \n).
    # Пустая строка в конце отделяет заголовки от тела запроса.
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {domain}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    try:
        conn.sendall(request.encode("ascii"))

        response = b""
        ttfb_ms = None

        while True:
            chunk = conn.recv(4096)

            if ttfb_ms is None:
                # Первый непустой chunk — это и есть TTFB.
                # Даже если chunk окажется b"" (сервер сразу закрыл
                # соединение), мы всё равно фиксируем момент первого
                # ответа сокета, а не молчим до конца while.
                ttfb_ms = (time.perf_counter() - start) * 1000

            if not chunk:
                # Пустые байты — сервер закрыл соединение,
                # это наш сигнал, что ответ получен полностью.
                break

            response += chunk

        elapsed_ms = (time.perf_counter() - start) * 1000

        if not response:
            info.update(
                success=False,
                elapsed_ms=elapsed_ms,
                ttfb_ms=ttfb_ms if ttfb_ms is not None else -1.0,
                error_type="EmptyResponse",
                explanation="The server closed the connection without sending any data.",
                recommendation="Check whether the server expects a different request format or hostname.",
            )
            return None, info

        # Заголовки отделены от тела пустой строкой \r\n\r\n.
        # Если разделителя нет (например, тело пришло сразу без заголовков) —
        # считаем, что заголовков в ответе нет вовсе.
        head, _, _body = response.partition(b"\r\n\r\n")
        header_lines = head.split(b"\r\n")

        # Статус-строка — это первая строка блока заголовков.
        # Пример: b"HTTP/1.1 302 Found"
        status_line = header_lines[0].decode("ascii", errors="replace")

        try:
            status_code = int(status_line.split(" ")[1])
        except (IndexError, ValueError):
            info.update(
                success=False,
                elapsed_ms=elapsed_ms,
                ttfb_ms=ttfb_ms,
                error_type="MalformedResponse",
                explanation=f"Could not parse a valid HTTP status line: {status_line!r}",
                recommendation="The server response does not look like standard HTTP/1.1.",
            )
            return None, info

        # Разбираем остальные строки в словарь заголовков.
        # Ключи приводим к нижнему регистру — HTTP-заголовки регистронезависимы,
        # сервер может прислать и "Location", и "location".
        headers = {}
        for line in header_lines[1:]:
            if not line:
                continue
            decoded = line.decode("ascii", errors="replace")
            if ": " not in decoded:
                continue
            key, _, value = decoded.partition(": ")
            headers[key.lower()] = value

        response_info = {
            "status_code": status_code,
            "status_line": status_line,
            "raw_size_bytes": len(response),
        }

        if 300 <= status_code < 400:
            location = headers.get("location", "")
            info.update(
                success=True,
                elapsed_ms=elapsed_ms,
                ttfb_ms=ttfb_ms,
                error_type="",
                explanation=(
                    f"Server responded with {status_code} and redirects to "
                    f"'{location}'." if location else
                    f"Server responded with {status_code}, but no Location header was provided."
                ),
                recommendation=(
                    "This is a redirect, not a failure — confirm the destination "
                    "is the expected one for this target."
                ),
            )
            response_info["status_category"] = "redirect"
            response_info["location"] = location
            return response_info, info

        if status_code >= 500:
            info.update(
                success=False,
                elapsed_ms=elapsed_ms,
                ttfb_ms=ttfb_ms,
                error_type=f"HTTP_{status_code}",
                explanation=f"Server responded with {status_code}, indicating a server-side application error.",
                recommendation="Check application logs, backend service health and recent deployments.",
            )
            return response_info, info

        info.update(
            success=True,
            elapsed_ms=elapsed_ms,
            ttfb_ms=ttfb_ms,
            explanation=f"Server responded with {status_code}.",
            recommendation="No HTTP problems detected." if status_code < 400 else
                            "Client-side error status — check the request path and parameters.",
        )
        return response_info, info

    except TimeoutError as e:
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="TimeoutError",
            explanation=f"The HTTP request to '{domain}' timed out. OS message: {e}",
            recommendation="Check server load, network latency and whether the app is responding at all.",
        )

    except OSError as e:
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type=type(e).__name__,
            explanation=f"The operating system reported an error during the HTTP request: {e}",
            recommendation="Check the connection state — it may have been closed by a previous layer.",
        )

    except Exception as e:
        # Последний защитный слой — как в остальных функциях уровня.
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type=type(e).__name__,
            explanation=f"An unexpected error occurred during the HTTP request: {e}",
            recommendation="Check the error type and message for further diagnosis.",
        )

    return None, info