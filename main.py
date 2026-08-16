import socket
import time
import json


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


def tcp_handshake(ip: str) -> list[dict[str, str | bool | None | float | int]] | None:
    """TCP Handshake"""
    ports_to_check = {443}
    try:
        ports_to_check.update(map(int, input("Type ports you want to check, except 443: ").split()))
    except ValueError:
        print("Invalid port number, type smth like: 8080 1010 1443 65000")

    logs = []


    for port in ports_to_check:
        cur = {
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
            print(f"TCP handshake to port {port} in {elapsed * 1000:.2f} ms")
            conn.close()
            cur["success"] = True
            cur["elapsed_ms"] = elapsed * 1000
            cur["error_type"] = ""
            cur["explanation"] = "Everything works properly!"
            cur["recommendation"] = "Chill, it's okay)"
            logs.append(cur)
        except ConnectionRefusedError:
            elapsed = time.perf_counter() - start
            print(f"Port {port} closed/service doesn't work/Another port required")
            cur["elapsed_ms"] = elapsed * 1000
            cur["success"] = False
            cur["error_type"] = "Connection refused"
            cur["explanation"] = "Port closed or service doesn't work"
            cur["recommendation"] = "Check servers, perhaps, they don't work right now. Check firewall settings or your web-server configs. To sum up: check, if the port opened"
            logs.append(cur)
        except ConnectionResetError:
            elapsed = time.perf_counter() - start
            print("We got RST packet, seems like firewall block our requests/service fall while starting")
            cur["elapsed_ms"] = elapsed * 1000
            cur["success"] = False
            cur["error_type"] = "Connection Reset"
            cur["explanation"] = "We got an RST packet, seems like smth in the middle don't let us to connect!"
            cur["recommendation"] = "Try to change IP or see hoster's rule/routing"
            logs.append(cur)
        except ConnectionAbortedError:
            print("Seems like rate limitations/local troubles with your machine")
            elapsed = time.perf_counter() - start
            cur["elapsed_ms"] = elapsed * 1000
            cur["success"] = False
            cur["error_type"] = "Connection Aborted"
            cur["explanation"] = "Service skipped our packets, seems like rate limiting or local stack problems"
            cur["recommendation"] = "Try to again later, try turning on/off WIFI-GSM, use another machine"
            logs.append(cur)
        except TimeoutError:
            print("Troubles with network, host unavailable or overloaded!")
            elapsed = time.perf_counter() - start
            cur["elapsed_ms"] = elapsed * 1000
            cur["success"] = False
            cur["error_type"] = "We got Timeout!"
            cur["explanation"] = "Too much time passed and we still have no returns"
            cur["recommendation"] = "See, if current site works in your region or check your provider's problems, perhaps, the service or network is overloaded"
            logs.append(cur)
        except OSError:
            print("Network error, host unavailable!")
            elapsed = time.perf_counter() - start
            cur["elapsed_ms"] = elapsed * 1000
            cur["success"] = False
            cur["error_type"] = "OS errors"
            cur["explanation"] = "We caught an OS error"
            cur["recommendation"] = "Try using another machine/check your current one"
            logs.append(cur)

    return logs


# Program starts
domain = input("Enter the domain: ")
skipping = input(f"Checking: {domain}, press enter to continue...")

ip = dns_resolve(domain)
tcp_dump = tcp_handshake(ip)

with open("tcp_dump.json", "w", encoding="utf-8") as f:
    json.dump(tcp_dump, f, indent=2, ensure_ascii=False)

print("Results saved to tcp_dump.json")