"""

Returning tcp_connection | None, logs

info = {
    "port": port,
    "success": None,
    "elapsed_ms": -1.0,
    "error_type": "",
    "explanation": "",
    "recommendation": "",
}

"""

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
    try:
        conn = socket.create_connection((ip, port), timeout=2)
        elapsed = time.perf_counter() - start
        info.update(
            success=True,
            elapsed_ms=elapsed * 1000,
            explanation="Everything works properly!",
            recommendation="Chill, it's okay)",
        )
        # Возвращаем ЖИВОЕ соединение — оно понадобится следующему слою (TLS)
        return conn, info
    except ConnectionRefusedError:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="Connection refused",
            explanation="Port closed or service doesn't work",
            recommendation="Check firewall settings or your web-server configs",
        )
    except ConnectionResetError:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="Connection Reset",
            explanation="We got an RST packet, seems like smth in the middle doesn't let us connect!",
            recommendation="Try to change IP or see hoster's rule/routing",
        )
    except ConnectionAbortedError:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="Connection Aborted",
            explanation="Service skipped our packets, seems like rate limiting",
            recommendation="Try again later, try turning WIFI off/on, use another machine",
        )
    except TimeoutError:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="Timeout",
            explanation="Too much time passed and we still have no response",
            recommendation="Check if the site works in your region or check your provider",
        )
    except OSError as e:
        elapsed = time.perf_counter() - start
        info.update(
            success=False, elapsed_ms=elapsed * 1000,
            error_type="OS error",
            explanation=f"We caught an OS error: {e}",
            recommendation="Try using another machine/check your current one",
        )


    return None, info # соединения нет — возвращаем None вместо него