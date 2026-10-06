#!/usr/bin/env python3
"""
IP Address Information Tool
Developed by: 4rch-M4g

Look up details about an IP address or hostname: validation, address
classification, reverse DNS, geolocation, ISP/ASN and timezone.

Uses only the Python standard library (no pip installs required).

Usage:
    python ip_info.py 8.8.8.8
    python ip_info.py example.com
    python ip_info.py            # looks up your own public IP
    python ip_info.py -f ips.txt # one IP/hostname per line
    python ip_info.py 1.1.1.1 --json
    python ip_info.py 8.8.8.8 --save results.json
"""

import argparse
import ipaddress
import json
import socket
import sys
import urllib.error
import urllib.request

__author__ = "4rch-M4g"
__version__ = "1.0.0"

TIMEOUT = 8
USER_AGENT = f"ip-info-tool/{__version__} (by {__author__})"

# --------------------------------------------------------------------------- #
# Terminal styling
# --------------------------------------------------------------------------- #
USE_COLOR = sys.stdout.isatty()


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else str(text)


BANNER = r"""
  ___ ____   ___        __
 |_ _|  _ \ |_ _|_ __  / _| ___
  | || |_) | | || '_ \| |_ / _ \
  | ||  __/  | || | | |  _| (_) |
 |___|_|    |___|_| |_|_|  \___/
   IP Address Information Tool
   Developed by: 4rch-M4g
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_target(target):
    """Return a valid IP string from an IP or hostname. Raises ValueError."""
    target = target.strip()
    try:
        return str(ipaddress.ip_address(target))
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(target, None)
        return infos[0][4][0]
    except socket.gaierror:
        raise ValueError(f"'{target}' is not a valid IP address or resolvable hostname")


def get_public_ip():
    for url in ("https://api.ipify.org?format=json", "https://ipwho.is/"):
        try:
            data = http_get_json(url)
            ip = data.get("ip")
            if ip:
                return ip
        except Exception:
            continue
    raise RuntimeError("Could not determine your public IP (check your connection).")


def classify(ip_str):
    ip = ipaddress.ip_address(ip_str)
    return {
        "version": f"IPv{ip.version}",
        "is_private": ip.is_private,
        "is_global": ip.is_global,
        "is_loopback": ip.is_loopback,
        "is_multicast": ip.is_multicast,
        "is_link_local": ip.is_link_local,
        "is_reserved": ip.is_reserved,
        "is_unspecified": ip.is_unspecified,
        "reverse_pointer": ip.reverse_pointer,
    }


def reverse_dns(ip_str):
    try:
        return socket.gethostbyaddr(ip_str)[0]
    except (socket.herror, socket.gaierror, OSError):
        return None


# --------------------------------------------------------------------------- #
# Geolocation providers (normalised to a common dict)
# --------------------------------------------------------------------------- #
def provider_ipwhois(ip):
    d = http_get_json(f"https://ipwho.is/{ip}")
    if not d.get("success", False):
        raise RuntimeError(d.get("message", "ipwho.is lookup failed"))
    conn = d.get("connection", {}) or {}
    tz = d.get("timezone", {}) or {}
    return {
        "provider": "ipwho.is",
        "continent": d.get("continent"),
        "country": d.get("country"),
        "country_code": d.get("country_code"),
        "region": d.get("region"),
        "city": d.get("city"),
        "postal": d.get("postal"),
        "latitude": d.get("latitude"),
        "longitude": d.get("longitude"),
        "timezone": tz.get("id"),
        "utc_offset": tz.get("utc"),
        "asn": f"AS{conn['asn']}" if conn.get("asn") else None,
        "organization": conn.get("org"),
        "isp": conn.get("isp"),
        "domain": conn.get("domain"),
    }


def provider_ipapi(ip):
    fields = ("status,message,continent,country,countryCode,regionName,city,"
              "zip,lat,lon,timezone,offset,isp,org,as,mobile,proxy,hosting")
    d = http_get_json(f"http://ip-api.com/json/{ip}?fields={fields}")
    if d.get("status") != "success":
        raise RuntimeError(d.get("message", "ip-api lookup failed"))
    return {
        "provider": "ip-api.com",
        "continent": d.get("continent"),
        "country": d.get("country"),
        "country_code": d.get("countryCode"),
        "region": d.get("regionName"),
        "city": d.get("city"),
        "postal": d.get("zip"),
        "latitude": d.get("lat"),
        "longitude": d.get("lon"),
        "timezone": d.get("timezone"),
        "utc_offset": d.get("offset"),
        "asn": d.get("as"),
        "organization": d.get("org"),
        "isp": d.get("isp"),
        "is_mobile": d.get("mobile"),
        "is_proxy": d.get("proxy"),
        "is_hosting": d.get("hosting"),
    }


PROVIDERS = (provider_ipwhois, provider_ipapi)


def geolocate(ip):
    errors = []
    for provider in PROVIDERS:
        try:
            return provider(ip)
        except (urllib.error.URLError, socket.timeout, RuntimeError, ValueError) as e:
            errors.append(f"{provider.__name__}: {e}")
    raise RuntimeError("All lookup providers failed -> " + " | ".join(errors))


# --------------------------------------------------------------------------- #
# Main lookup
# --------------------------------------------------------------------------- #
def lookup(target, offline=False):
    result = {"query": target}
    try:
        ip = resolve_target(target)
    except ValueError as e:
        result["error"] = str(e)
        return result

    result["ip"] = ip
    result["classification"] = classify(ip)
    result["reverse_dns"] = reverse_dns(ip)

    if offline:
        return result

    info = result["classification"]
    if not info["is_global"]:
        result["geo"] = None
        result["note"] = ("Non-public address (private/loopback/reserved); "
                          "no geolocation data exists for it.")
        return result

    try:
        result["geo"] = geolocate(ip)
    except RuntimeError as e:
        result["geo"] = None
        result["error"] = str(e)
    return result


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def row(label, value):
    if value in (None, "", []):
        value = "N/A"
    print(f"  {c(label.ljust(16), '36')} {value}")


def yes_no(v):
    return "Yes" if v else "No"


def print_report(res):
    print(c("=" * 60, "90"))
    if "ip" not in res:
        print(c(f"  [!] {res['error']}", "31"))
        return

    print(c(f"  Target: {res['query']}  ->  {res['ip']}", "1;32"))
    print(c("=" * 60, "90"))

    cl = res["classification"]
    print(c("\n  [ Address Details ]", "1;33"))
    row("Version", cl["version"])
    row("Public (global)", yes_no(cl["is_global"]))
    row("Private", yes_no(cl["is_private"]))
    row("Loopback", yes_no(cl["is_loopback"]))
    row("Multicast", yes_no(cl["is_multicast"]))
    row("Link-local", yes_no(cl["is_link_local"]))
    row("Reserved", yes_no(cl["is_reserved"]))
    row("Reverse DNS", res.get("reverse_dns"))
    row("PTR record", cl["reverse_pointer"])

    geo = res.get("geo")
    if geo:
        print(c("\n  [ Location ]", "1;33"))
        row("Continent", geo.get("continent"))
        row("Country", f"{geo.get('country')} ({geo.get('country_code')})")
        row("Region", geo.get("region"))
        row("City", geo.get("city"))
        row("Postal code", geo.get("postal"))
        row("Coordinates", f"{geo.get('latitude')}, {geo.get('longitude')}")
        if geo.get("latitude") is not None:
            row("Map", f"https://www.google.com/maps?q={geo['latitude']},{geo['longitude']}")
        row("Timezone", geo.get("timezone"))

        print(c("\n  [ Network ]", "1;33"))
        row("ASN", geo.get("asn"))
        row("Organization", geo.get("organization"))
        row("ISP", geo.get("isp"))
        if geo.get("domain"):
            row("Domain", geo.get("domain"))
        for key, label in (("is_mobile", "Mobile"), ("is_proxy", "Proxy/VPN"),
                           ("is_hosting", "Hosting/DC")):
            if key in geo:
                row(label, yes_no(geo[key]))
        print(c(f"\n  Source: {geo['provider']}", "90"))

    if res.get("note"):
        print(c(f"\n  [i] {res['note']}", "34"))
    if res.get("error"):
        print(c(f"\n  [!] {res['error']}", "31"))
    print()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(
        prog="ip_info",
        description=f"IP Address Information Tool - developed by {__author__}",
    )
    p.add_argument("targets", nargs="*", help="IP address(es) or hostname(s); omit to use your public IP")
    p.add_argument("-f", "--file", help="file containing one IP/hostname per line")
    p.add_argument("-j", "--json", action="store_true", help="print results as JSON")
    p.add_argument("-s", "--save", metavar="FILE", help="save results to a JSON file")
    p.add_argument("--offline", action="store_true",
                   help="skip online geolocation (validation, classification and DNS only)")
    p.add_argument("--no-color", action="store_true", help="disable colored output")
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__} by {__author__}")
    return p


def main():
    global USE_COLOR
    args = build_parser().parse_args()
    if args.no_color or args.json:
        USE_COLOR = False

    targets = list(args.targets)
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                targets += [ln.strip() for ln in fh
                            if ln.strip() and not ln.startswith("#")]
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 1

    if not targets:
        if args.offline:
            print("Offline mode needs at least one target.", file=sys.stderr)
            return 1
        try:
            targets = [get_public_ip()]
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if not args.json:
        print(c(BANNER, "1;35"))

    results = []
    for t in targets:
        res = lookup(t, offline=args.offline)
        results.append(res)
        if not args.json:
            print_report(res)

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))

    if args.save:
        try:
            with open(args.save, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2)
            if not args.json:
                print(c(f"  Results saved to {args.save}", "32"))
        except OSError as e:
            print(f"Could not save results: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)