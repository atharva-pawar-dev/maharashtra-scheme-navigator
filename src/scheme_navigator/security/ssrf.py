from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

OFFICIAL_MAHARASHTRA_DOMAIN_SUFFIXES = (
    "maharashtra.gov.in",
    "mahaonline.gov.in",
    "gov.in",
    "nic.in",
)

BLOCKED_INTERNAL_PORTS = {22, 25, 8080, 8000, 6333, 6379, 11434, 27017, 5432, 3306}


def is_private_or_loopback_ip(ip_str: str) -> bool:
    """Check if an IP address belongs to loopback, link-local, private, or multicast ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_safe_url(url: str, enforce_allowlist: bool = True) -> str:
    """Validate an external source or portal URL against SSRF, internal network scanning,

    and protocol injection attacks.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()

    # 1. Strict protocol requirement: HTTPS only
    if not url.startswith("https://"):
        raise ValueError("Security violation: Only secure HTTPS URLs are permitted.")

    parsed = urlparse(url)

    # 2. Reject embedded userinfo (e.g. https://user:pass@evil.com)
    if parsed.username or parsed.password:
        raise ValueError("Security violation: URLs containing userinfo are strictly disallowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing hostname.")

    hostname = hostname.casefold()

    # 3. Reject forbidden hostnames
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}:
        raise ValueError("Security violation: Access to local/internal hostnames is blocked.")

    # 4. Check port
    if parsed.port and parsed.port in BLOCKED_INTERNAL_PORTS:
        raise ValueError(f"Security violation: Target port {parsed.port} is blocked.")

    # 5. Direct IP check
    if is_private_or_loopback_ip(hostname):
        raise ValueError(f"Security violation: Private IP address {hostname} is blocked.")

    # 6. Domain allowlist check for public government sources
    if enforce_allowlist:
        allowed = any(
            hostname == suffix or hostname.endswith(f".{suffix}")
            for suffix in OFFICIAL_MAHARASHTRA_DOMAIN_SUFFIXES
        )
        if not allowed:
            raise ValueError(
                f"Security violation: Domain '{hostname}' is not in the official government allowlist ({', '.join(OFFICIAL_MAHARASHTRA_DOMAIN_SUFFIXES)})."
            )

    # 7. DNS pre-resolution check against DNS rebinding & internal network routing
    try:
        port = parsed.port or 443
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_info:
            resolved_ip = sockaddr[0]
            if is_private_or_loopback_ip(resolved_ip):
                raise ValueError(
                    f"Security violation: Hostname '{hostname}' resolves to prohibited private/internal IP {resolved_ip}."
                )
    except socket.gaierror:
        # For offline testing where DNS is unreachable, step 5 already checked literal IPs
        pass

    return url


class SSRFSafeSyncBackend:
    """Network backend for httpcore that eliminates DNS rebinding TOCTOU gaps.

    It performs DNS resolution at TCP connection time, validates every resolved
    IP (IPv4 and IPv6) against private/loopback/link-local ranges, connects
    directly to the safe IP, and verifies the connected socket's peer IP.
    SNI and TLS certificate validation are preserved via server_hostname.
    """

    def __init__(self) -> None:
        import httpcore._backends.sync
        self._delegate = httpcore._backends.sync.SyncBackend()

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: typing.Iterable[typing.Any] | None = None,
    ):
        import httpcore
        from httpcore._backends.sync import SyncStream
        from httpcore._exceptions import ConnectError, ConnectTimeout, ExceptionMapping, map_exceptions

        if socket_options is None:
            socket_options = []

        # 1. Resolve host and check all addresses against SSRF / internal IP ranges
        try:
            addr_info = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise ConnectError(f"DNS resolution failed for {host}: {exc}") from exc

        if not addr_info:
            raise ConnectError(f"DNS resolution returned no addresses for {host}")

        safe_addr = None
        for family, socktype, proto, canonname, sockaddr in addr_info:
            resolved_ip = sockaddr[0]
            if is_private_or_loopback_ip(resolved_ip):
                raise ConnectError(
                    f"SSRF violation: Host '{host}' resolved to forbidden private/internal IP '{resolved_ip}'"
                )
            if safe_addr is None:
                safe_addr = (resolved_ip, port)

        if safe_addr is None:
            raise ConnectError(f"No valid public address found for {host}")

        source_address = None if local_address is None else (local_address, 0)
        exc_map: ExceptionMapping = {
            socket.timeout: ConnectTimeout,
            OSError: ConnectError,
        }

        # 2. Connect directly to the validated IP address
        with map_exceptions(exc_map):
            sock = socket.create_connection(
                safe_addr,
                timeout,
                source_address=source_address,
            )
            # 3. Post-connection peer check
            peer_ip = sock.getpeername()[0]
            if is_private_or_loopback_ip(peer_ip):
                sock.close()
                raise ConnectError(
                    f"SSRF violation: Connected socket peer IP '{peer_ip}' is private/loopback"
                )

            for option in socket_options:
                sock.setsockopt(*option)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # 4. Return SyncStream; start_tls will receive server_hostname=host for SNI & TLS validation
        return SyncStream(sock)


class SSRFSafeTransport:
    """HTTPX Transport wrapped with SSRFSafeSyncBackend to prevent DNS rebinding."""

    def __new__(cls, *args, **kwargs):
        import httpx
        transport = httpx.HTTPTransport(*args, **kwargs)
        if hasattr(transport, "_pool") and hasattr(transport._pool, "_network_backend"):
            transport._pool._network_backend = SSRFSafeSyncBackend()
        return transport

