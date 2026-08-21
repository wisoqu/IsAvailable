import json
from network.ip_resolve import dns_resolve
from network.tcp_handshake import tcp_handshake
from network.tls_handshake import tls_handshake



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

ip, result = dns_resolve(domain)
if ip is None:
    print("IP is none")
    exit()

# Сбор портов теперь здесь, а не внутри tcp_handshake —
# это вопрос "что мы вообще хотим проверить", а не "как проверить одну вещь"
if ip is not None:
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