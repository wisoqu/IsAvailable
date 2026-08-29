import json
from urllib.parse import urlparse

from network.ip_resolve import dns_resolve
from network.tcp_handshake import tcp_handshake
from network.tls_handshake import tls_handshake
from network.http_check import http_check

# Порты, для которых имеет смысл пробовать TLS.
# Пользователь не должен сам разбираться, какие порты HTTPS —
# это должен решать инструмент.
TLS_PORTS = {443, 8443, 8843, 9443}

LOGS = {}


# Ввод адреса — принимаем как голый домен, так и URL с путём
# (google.com, https://google.com, google.com/search — всё ок)
raw_input_url = input("Enter the domain or URL: ")
skipping = input(f"Checking: {raw_input_url}, press enter to continue...")

parsed = urlparse(raw_input_url if "://" in raw_input_url else "https://" + raw_input_url)
domain = parsed.netloc
path = parsed.path or "/"
if parsed.query:
    path += "?" + parsed.query

LOGS["domain"] = domain
LOGS["path"] = path

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
    LOGS["ports"][port] = {}

    tcp_conn, tcp_logs = tcp_handshake(ip, port)
    LOGS["ports"][port]["tcp_log"] = tcp_logs

    # Соединение, которое пойдёт дальше в HTTP-слой.
    # По умолчанию — голый TCP; если порт требует TLS, попробуем его поднять.
    http_conn = tcp_conn

    if port in TLS_PORTS:
        tls_conn, tls_logs = tls_handshake(tcp_conn, domain)
        LOGS["ports"][port]["tls_log"] = tls_logs

        # Если TLS упал, tls_conn == None. http_check сам корректно
        # обработает conn is None — отдельно проверять здесь не нужно,
        # эта защита уже реализована внутри http_check.
        http_conn = tls_conn

    http_response, http_logs = http_check(http_conn, domain, path)
    LOGS["ports"][port]["http_log"] = http_logs

with open("tcp_dump.json", "w", encoding="utf-8") as file:
    json.dump(LOGS, file, indent=4, ensure_ascii=False)