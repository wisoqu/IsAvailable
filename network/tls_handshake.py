import socket
import time
import ssl


def tls_handshake(
    conn: socket.socket,
    domain: str
) -> tuple[ssl.SSLSocket | None, dict]:
    """Оборачивает уже открытое TCP-соединение в TLS.
    Возвращает (ssl-соединение или None, инфо).
    """

    info = {
        "success": None,
        "elapsed_ms": -1.0,
        "error_type": "",
        "explanation": "",
    }

    start = time.perf_counter()

    # Проверяем соединение до вызова SSL
    if conn is None:
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidConnection",
            explanation="TCP connection is None. TLS handshake cannot be started.",
        )
        return None, info

    if not isinstance(conn, socket.socket):
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidConnection",
            explanation=(
                f"Expected socket.socket, but received "
                f"{type(conn).__name__}."
            ),
        )
        return None, info

    # Проверяем домен
    if not isinstance(domain, str) or not domain.strip():
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="InvalidDomain",
            explanation="Domain must be a non-empty string.",
        )
        return None, info

    domain = domain.strip()

    try:
        context = ssl.create_default_context()

        ssl_conn = context.wrap_socket(
            conn,
            server_hostname=domain,
        )

        elapsed = time.perf_counter() - start

        info.update(
            success=True,
            elapsed_ms=elapsed * 1000,
            explanation="TLS handshake successful.",
        )

        # Возвращаем ЖИВОЕ TLS-соединение.
        return ssl_conn, info

    except ssl.SSLCertVerificationError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="CertificateVerificationError",
            explanation=(
                f"TLS certificate verification failed for '{domain}'. "
                f"The certificate may be invalid, expired, untrusted, "
                f"or issued for another hostname. SSL message: {e}"
            ),
        )

    except ssl.SSLError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="SSLError",
            explanation=(
                f"TLS handshake failed for '{domain}'. "
                f"The server may not support the expected TLS configuration, "
                f"or the connection may have been interrupted. "
                f"SSL message: {e}"
            ),
        )

    except TimeoutError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="TimeoutError",
            explanation=(
                f"TLS handshake with '{domain}' exceeded the socket timeout. "
                f"OS message: {e}"
            ),
        )

    except OSError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type=type(e).__name__,
            explanation=(
                f"The operating system reported an error during "
                f"the TLS handshake: {e}"
            ),
        )

    except ValueError as e:
        elapsed = time.perf_counter() - start

        info.update(
            success=False,
            elapsed_ms=elapsed * 1000,
            error_type="ValueError",
            explanation=(
                f"Invalid value was provided to the TLS layer: {e}"
            ),
        )

    except Exception as e:
        # Последний защитный слой.
        info.update(
            success=False,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type=type(e).__name__,
            explanation=(
                f"An unexpected error occurred during the TLS handshake: {e}"
            ),
        )

    return None, info