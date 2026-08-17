import socket
import time
import json
import ssl


def dns_resolve(domain: str) -> str:
    """Getting IP address"""
    ip = ""
    while not ip:
        start = time.perf_counter()  # start counting
        try:
            ip  = socket.gethostbyname(domain)
            elapsed = time.perf_counter() - start  # end counting
            print(f"IP address: {ip}, time: {elapsed * 1000:.2f} ms")
        except socket.gaierror:
            elapsed = time.perf_counter() - start  # end counting
            print(f"Failed to resolve IP address, time: {elapsed * 1000:.2f} ms. Reason: domain does not exist!")
            domain = input("Enter the domain AGAIN: ")
        finally:
            print("Ended IP check with the result:", "success" if ip else "failure, try again!")

    return ip

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


def check_port(domain: str, ip: str, port: int) -> dict:
    """Прогоняет все слои по порядку для одного порта: TCP -> TLS."""
    result = {"port": port}

    conn, tcp_info = tcp_handshake(ip, port)
    result["tcp"] = tcp_info

    if conn is None:
        # TCP не удался — TLS проверять физически не на чём, соединения нет
        result["tls"] = None
        return result

    ssl_conn, tls_info = tls_handshake(conn, domain)
    result["tls"] = tls_info

    # Закрываем то соединение, которое реально осталось открытым
    if ssl_conn is not None:
        ssl_conn.close()
    else:
        conn.close()

    return result




# Program starts
domain = input("Enter the domain: ")
skipping = input(f"Checking: {domain}, press enter to continue...")

ip = dns_resolve(domain)

# Сбор портов теперь здесь, а не внутри tcp_handshake —
# это вопрос "что мы вообще хотим проверить", а не "как проверить одну вещь"
ports_to_check = {443}
try:
    ports_to_check.update(map(int, input("Type ports you want to check, except 443: ").split()))
except ValueError:
    print("Invalid port number, type smth like: 8080 1010 1443 65000")

results = []
for port in ports_to_check:
    results.append(check_port(domain, ip, port))

with open("tcp_dump.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Results saved to tcp_dump.json")