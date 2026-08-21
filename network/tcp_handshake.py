import socket
import time


def tcp_handshake(ip: str, port: int) -> tuple[socket.socket | None, dict]:
    """Проверяет ОДИН порт. Возвращает (соединение или None, инфо о попытке)."""

    info = {
        "port": port,
        "success": None,
        "elapsed_ms": -1.0,
        "error_type": "",
        "explanation": "",
        "recommendation": "",
    }

    start = time.perf_counter()
    conn = None

    # Проверяем IP до обращения к socket
    if not isinstance(ip, str) or not ip.strip():
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="Invalid IP",
            explanation="IP address is empty or has an invalid type.",
            recommendation="Make sure DNS resolution completed successfully before TCP check.",
        )
        return None, info

    # Проверяем порт до обращения к socket
    if not isinstance(port, int) or isinstance(port, bool):
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="Invalid port",
            explanation="Port must be an integer.",
            recommendation="Use a port number from 1 to 65535.",
        )
        return None, info

    if not 1 <= port <= 65535:
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="Invalid port",
            explanation=f"Port {port} is outside the valid TCP port range.",
            recommendation="Use a port number from 1 to 65535.",
        )
        return None, info

    try:
        conn = socket.create_connection((ip.strip(), port), timeout=2)

        elapsed = time.perf_counter() - start

        info.update(
            success=True,
            elapsed_ms=elapsed * 1000,
            explanation="TCP connection established successfully.",
            recommendation="No TCP problems detected.",
        )

        # Возвращаем ЖИВОЕ соединение — оно понадобится следующему слою (TLS)
        return conn, info

    except ConnectionRefusedError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="ConnectionRefusedError",
            explanation=(
                f"The remote host actively refused the TCP connection "
                f"to port {port}. The service may be unavailable or "
                f"the port may be closed. OS message: {e}"
            ),
            recommendation=(
                "Check whether the service is running and whether "
                "the port is allowed by the server firewall."
            ),
        )

    except ConnectionResetError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="ConnectionResetError",
            explanation=(
                "The TCP connection was reset by the remote host "
                "or by a device between you and the host. "
                f"OS message: {e}"
            ),
            recommendation=(
                "Check the server, firewall, routing and possible "
                "network filtering. If the problem is temporary, try again."
            ),
        )

    except ConnectionAbortedError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="ConnectionAbortedError",
            explanation=(
                "The TCP connection was aborted before it could be "
                f"established successfully. OS message: {e}"
            ),
            recommendation=(
                "Check the network connection and server availability. "
                "If the error repeats, investigate firewall or network filtering."
            ),
        )

    except TimeoutError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="TimeoutError",
            explanation=(
                f"The TCP connection to port {port} did not complete "
                f"within the 2-second timeout. OS message: {e}"
            ),
            recommendation=(
                "Check network connectivity, routing, firewall rules "
                "and whether the service is reachable from your region."
            ),
        )

    except OSError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type=type(e).__name__,
            explanation=(
                f"The operating system reported an error while trying "
                f"to establish the TCP connection: {e}"
            ),
            recommendation=(
                "Check network connectivity, routing, firewall settings "
                "and the availability of the remote service."
            ),
        )

    except Exception as e:
        # Последний защитный слой.
        # Непредвиденная ошибка не должна уронить весь диагностический pipeline.
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type=type(e).__name__,
            explanation=(
                f"An unexpected error occurred during the TCP handshake: {e}"
            ),
            recommendation=(
                "Check the error type and message. "
                "This error was not recognized as a standard TCP failure."
            ),
        )

    # Если соединение каким-либо образом было создано,
    # но произошла ошибка после этого — не оставляем socket открытым.
    if conn is not None:
        try:
            conn.close()
        except OSError:
            pass

    return None, info