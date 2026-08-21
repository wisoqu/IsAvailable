"""

Returning ssl_connection | None, logs

logs = {
    "success": None,
    "elapsed_ms": -1.0,
    "error_type": "",
    "explanation": "",
}

"""

import socket
import time
import ssl



def tls_handshake(conn: socket.socket, domain: str) -> tuple[ssl.SSLSocket | None, dict]:
    """Оборачивает уже открытое TCP-соединение в TLS. Возвращает (ssl-соединение или None, инфо)."""
    info = {
        "success": None,
        "elapsed_ms": -1.0,
        "error_type": "",
        "explanation": "",
    }
    context = ssl.create_default_context()
    start = time.perf_counter()
    try:
        ssl_conn = context.wrap_socket(conn, server_hostname=domain)
        elapsed = time.perf_counter() - start
        info.update(success=True, elapsed_ms=elapsed * 1000, explanation="TLS handshake successful")
        return ssl_conn, info
    except ssl.SSLCertVerificationError as e:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="Certificate verification failed",
            explanation=f"Certificate problem: {e}",
        )
        return None, info
    except ssl.SSLError as e:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="SSL error",
            explanation=f"TLS handshake failed: {e}",
        )
        return None, info