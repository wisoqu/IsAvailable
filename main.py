import socket
import time
from operator import truediv


def dns_resolve(domain: str) -> None | str:
    """Getting IP address"""
    ip = 0
    start = time.perf_counter() # start counting
    try:
        ip  = socket.gethostbyname(domain)
        print(f"IP address: {ip}")
    except socket.gaierror:
        print("Failed to resolve IP address")
    finally:
        print("Ended IP check with the result:", "success" if ip else "failure")

    elapsed = time.perf_counter() - start # end counting
    print(f"DNS resolved in {elapsed * 1000:.2f} ms")


def tcp_handshake(domain: str) -> None | str:
    """TCP Handshake"""
    succeed = False
    start = time.perf_counter() # start counting

    try:
        socket.create_connection((domain, 443), timeout=2)
        succeed = True
    except (socket.timeout, OSError, ConnectionRefusedError, ConnectionResetError) as e:
        print("Failed to create connection")
    finally:
        print("Ended connection check with the result:", "success" if succeed else "failure")


    elapsed = time.perf_counter() - start # end counting
    print(f"TCP handshake in {elapsed * 1000:.2f} ms")




# Program starts
domain = input("Enter the domain: ")
print(f"Checking: {domain}")

dns_resolve(domain)
tcp_handshake(domain)