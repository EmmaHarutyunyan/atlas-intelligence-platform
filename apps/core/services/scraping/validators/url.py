import ipaddress
import socket
from urllib.parse import urlparse

from apps.core.services.scraping.exceptions import InvalidURLError, UnsafeURLError

ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.google.internal.",
    "host.docker.internal",
}
MAX_REDIRECTS = 5


def _is_private_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


def resolve_public_host(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise InvalidURLError("The hostname could not be resolved.") from exc

    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise InvalidURLError("The hostname could not be resolved.")

    unsafe = [address for address in addresses if _is_private_ip(address)]
    if unsafe:
        raise UnsafeURLError("The URL resolves to a private or internal network address.")
    return addresses


def validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise InvalidURLError("A URL is required.")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise InvalidURLError("Only public HTTP and HTTPS URLs are supported.")
    if not parsed.hostname:
        raise InvalidURLError("The URL must contain a valid hostname.")
    if parsed.username or parsed.password:
        raise InvalidURLError("URLs containing embedded credentials are not allowed.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local"):
        raise UnsafeURLError("Local and internal hostnames are not allowed.")

    resolve_public_host(hostname)
    return parsed.geturl()
