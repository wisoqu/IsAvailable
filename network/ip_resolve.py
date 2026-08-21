"""

Returning ip | None, logs

info = {
    "success": False,
    "elapsed_ms": -1.0,
    "error_type": "",
    "explanation": "",
    "recommendation": "",
}

"""

import time
import socket


def dns_resolve(domain: str):
    info = {
        "success": False,
        "elapsed_ms": -1.0,
        "error_type": "",
        "explanation": "",
        "recommendation": "",
    }

    ip = None
    start = time.perf_counter()

    # Проверяем входные данные до DNS-запроса
    if not isinstance(domain, str):
        info.update(
            error_type="InvalidInput",
            explanation="The domain must be a string.",
            recommendation="Provide a domain name in the format 'example.com'.",
        )
        return None, info

    domain = domain.strip()

    if not domain:
        info.update(
            error_type="InvalidInput",
            explanation="The domain name is empty.",
            recommendation="Provide a domain name, for example 'example.com'.",
        )
        return None, info

    try:
        # Реальный DNS-запрос
        ip = socket.gethostbyname(domain)

        info.update(
            success=True,
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="",
            explanation=f"Domain '{domain}' was successfully resolved to IP address {ip}.",
            recommendation="No errors detected.",
        )

    except socket.gaierror as e:
        elapsed_ms = (time.perf_counter() - start) * 1000

        error_code = e.errno

        info["elapsed_ms"] = elapsed_ms

        if error_code == socket.EAI_NONAME:
            info.update(
                error_type="EAI_NONAME",
                explanation=(
                    f"DNS could not resolve the domain '{domain}'. "
                    "The name server reports that the domain does not exist "
                    "or that there is no suitable DNS record for it."
                ),
                recommendation=(
                    "Check whether the domain name is spelled correctly. "
                    "If the domain is correct, check its DNS records "
                    "and the DNS server being used."
                ),
            )

        elif error_code == socket.EAI_AGAIN:
            info.update(
                error_type="EAI_AGAIN",
                explanation=(
                    "The DNS request could not be completed temporarily. "
                    "This may be caused by a temporary DNS server "
                    "or network problem."
                ),
                recommendation=(
                    "Retry the request after a few seconds "
                    "and check your network connection."
                ),
            )

        elif error_code == socket.EAI_FAIL:
            info.update(
                error_type="EAI_FAIL",
                explanation=(
                    "The DNS server reported a permanent failure "
                    "while trying to resolve the domain name."
                ),
                recommendation=(
                    "Check the DNS server availability, the domain's DNS zone, "
                    "and your network configuration."
                ),
            )

        elif hasattr(socket, "EAI_FAMILY") and error_code == socket.EAI_FAMILY:
            info.update(
                error_type="EAI_FAMILY",
                explanation=(
                    "The DNS request used an unsupported address family."
                ),
                recommendation=(
                    "Check your IPv4/IPv6 configuration "
                    "and DNS request parameters."
                ),
            )

        else:
            info.update(
                error_type=f"DNS_ERROR_{error_code}",
                explanation=(
                    f"A DNS error occurred while resolving '{domain}'. "
                    f"System error code: {error_code}. "
                    f"OS message: {e}"
                ),
                recommendation=(
                    "Check your network connection, DNS configuration, "
                    "and DNS server availability."
                ),
            )

    except socket.timeout:
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="Timeout",
            explanation=(
                f"The DNS request for '{domain}' exceeded the allowed "
                "time limit."
            ),
            recommendation=(
                "Check your network connection and DNS server availability. "
                "Try using another DNS server."
            ),
        )

    except OSError as e:
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type="OSError",
            explanation=(
                "The operating system could not complete the DNS request. "
                f"OS message: {e}"
            ),
            recommendation=(
                "Check your network connection, DNS configuration, "
                "and system network settings."
            ),
        )

    except Exception as e:
        # Последний защитный слой:
        # функция не должна неожиданно уронить программу.
        info.update(
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_type=type(e).__name__,
            explanation=(
                "An unexpected error occurred during DNS resolution: "
                f"{e}"
            ),
            recommendation=(
                "Check the input data and system state. "
                "If the error persists, save its type and message "
                "for further diagnosis."
            ),
        )

    return ip, info