import json
from network.ip_resolve import dns_resolve
from network.tcp_handshake import tcp_handshake
from network.tls_handshake import tls_handshake

LOGS = {}


# Ввод домена
domain = input("Enter the domain: ")
skipping = input(f"Checking: {domain}, press enter to continue...")

LOGS["domain"] = domain

# Получение IP | None, логов
ip, ip_logs = dns_resolve(domain)
LOGS["ip"] = ip
LOGS["ip_logs"] = ip_logs


# Начинаем TCP/TLS, сразу же, ибо TCP отдает TLS соединение
ports_to_check = {443}
try:
    ports_to_check.update((map(int, input("Enter ports to check separated with space: ").split())))
except ValueError:
    print("Please enter a valid port")
    exit()

LOGS["ports"] = {}
for port in ports_to_check:
    tcp_conn, tcp_logs = tcp_handshake(ip,port)
    LOGS["ports"][port] = tcp_logs

    tls_conn, tls_logs = tls_handshake(tcp_conn,domain)
    LOGS["tls_handshake"] = tls_logs

with open("tcp_dump.json", "w", encoding="utf-8") as file:
    json.dump(LOGS, file, indent=4, ensure_ascii=False)