import socket
import time


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
            print(f"Failed to resolve IP address, time: {elapsed * 1000:.2f} ms")
            domain = input("Enter the domain AGAIN: ")
        finally:
            print("Ended IP check with the result:", "success" if ip else "failure, try again!")

    return ip


def tcp_handshake(ip: str) -> None | str:
    """TCP Handshake"""
    ports_to_check = {443}
    try:
        ports_to_check.update(map(int, input("Type ports you want to check, except 443: ").split()))
    except ValueError:
        print("Invalid port number")

    for port in ports_to_check:
        start = time.perf_counter()
        try:
            conn = socket.create_connection((ip, port), timeout=2)
            elapsed = time.perf_counter() - start
            print(f"TCP handshake to port {port} in {elapsed * 1000:.2f} ms")
            conn.close()
        except (socket.gaierror, OSError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError) as e:
            elapsed = time.perf_counter() - start
            print(f"Unable to connect to port: {port}, time: {elapsed * 1000:.2f} ms")


# Program starts
domain = input("Enter the domain: ")
skipping = input(f"Checking: {domain}, press enter to continue...")

ip = dns_resolve(domain)
tcp_handshake(ip)