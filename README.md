# IP Address Information Tool

> **Developed by 4rch-M4g**

A lightweight, dependency-free command-line tool that tells you everything useful about an IP address or hostname: validation, address type, reverse DNS, geolocation, ISP/ASN and timezone. Written in pure Python.

```
  ___ ____   ___        __
 |_ _|  _ \ |_ _|_ __  / _| ___
  | || |_) | | || '_ \| |_ / _ \
  | ||  __/  | || | | |  _| (_) |
 |___|_|    |___|_| |_|_|  \___/
   IP Address Information Tool
   Developed by: 4rch-M4g
```

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Options](#options)
- [Examples](#examples)
- [Sample Output](#sample-output)
- [JSON Output](#json-output)
- [Batch Mode](#batch-mode)
- [Data Sources](#data-sources)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Privacy & Disclaimer](#privacy--disclaimer)
- [Author](#author)

---

## Features

- **IPv4 and IPv6** support
- **Accepts IPs or hostnames:** domains are resolved automatically
- **Your own public IP:** run with no arguments to look yourself up
- **Address classification:** public, private, loopback, multicast, link-local, reserved
- **Reverse DNS** and PTR record
- **Geolocation:** continent, country, region, city, postal code, coordinates (with a map link), timezone
- **Network info:** ASN, organization, ISP, domain, plus mobile/proxy/hosting flags when available
- **Automatic fallback** between two lookup providers
- **Batch mode:** read targets from a file
- **JSON output** and file saving
- **Offline mode** for validation and classification only
- **Colored output** (auto-disabled when piped or with `--no-color`)
- **Zero dependencies:** Python standard library only

## Requirements

- Python **3.7+**
- Internet access for geolocation (not needed for `--offline`)
- Works on Linux, macOS and Windows

## Installation

No installation is needed:

```bash
git clone <your-repo-url>
cd <your-repo>
python ip_info.py 8.8.8.8
```

Or just save `ip_info.py` anywhere and run it. On Linux/macOS:

```bash
chmod +x ip_info.py
./ip_info.py 8.8.8.8
```

## Quick Start

```bash
python ip_info.py                 # your own public IP
python ip_info.py 8.8.8.8         # a specific IP
python ip_info.py example.com     # a hostname
python ip_info.py -f ips.txt      # many targets from a file
python ip_info.py 1.1.1.1 --json  # JSON output
```

## Options

| Option | Description |
|---|---|
| `targets` | One or more IP addresses or hostnames. Omit to look up your own public IP. |
| `-f`, `--file FILE` | Read targets from a file (one per line; blank lines and lines starting with `#` are ignored). |
| `-j`, `--json` | Print results as JSON. |
| `-s`, `--save FILE` | Save results to a JSON file. |
| `--offline` | Skip online geolocation (validation, classification and DNS only). |
| `--no-color` | Disable colored output. |
| `-v`, `--version` | Show version and author. |
| `-h`, `--help` | Show help. |

## Examples

### Look up an IP
```bash
python ip_info.py 8.8.8.8
```

### Look up several targets at once
```bash
python ip_info.py 8.8.8.8 1.1.1.1 example.com
```

### Look up your own public IP
```bash
python ip_info.py
```

### Check an IPv6 address
```bash
python ip_info.py 2606:4700:4700::1111
```

### Classify an address without internet access
```bash
python ip_info.py 192.168.1.10 --offline
```

### Save results
```bash
python ip_info.py 8.8.8.8 1.1.1.1 --save results.json
```

## Sample Output

```
============================================================
  Target: 8.8.8.8  ->  8.8.8.8
============================================================

  [ Address Details ]
  Version          IPv4
  Public (global)  Yes
  Private          No
  Loopback         No
  Multicast        No
  Link-local       No
  Reserved         No
  Reverse DNS      dns.google
  PTR record       8.8.8.8.in-addr.arpa

  [ Location ]
  Continent        North America
  Country          United States (US)
  Region           California
  City             Mountain View
  ...
  Timezone         America/Los_Angeles

  [ Network ]
  ASN              AS15169
  Organization     Google LLC
  ISP              Google LLC

  Source: ipwho.is
```

> The Location and Network values above are illustrative. Real results depend on the lookup provider and may differ.

For private or loopback addresses (for example `192.168.1.1` or `127.0.0.1`), the tool shows the address details and explains that no geolocation exists for non-public addresses.

## JSON Output

```bash
python ip_info.py 8.8.8.8 --json
```

```json
{
  "query": "8.8.8.8",
  "ip": "8.8.8.8",
  "classification": {
    "version": "IPv4",
    "is_private": false,
    "is_global": true,
    "is_loopback": false,
    "is_multicast": false,
    "is_link_local": false,
    "is_reserved": false,
    "is_unspecified": false,
    "reverse_pointer": "8.8.8.8.in-addr.arpa"
  },
  "reverse_dns": "dns.google",
  "geo": {
    "provider": "ipwho.is",
    "country": "United States",
    "country_code": "US",
    "region": "California",
    "city": "Mountain View",
    "latitude": 37.4,
    "longitude": -122.1,
    "timezone": "America/Los_Angeles",
    "asn": "AS15169",
    "organization": "Google LLC",
    "isp": "Google LLC"
  }
}
```

With a single target, a single object is printed. With multiple targets, a list is printed. Files written with `--save` always contain a list. If a lookup fails, the result includes an `"error"` field instead of crashing the run.

## Batch Mode

Create a text file with one target per line:

```text
# my targets
8.8.8.8
1.1.1.1
example.com
```

Then run:

```bash
python ip_info.py -f targets.txt --save report.json
```

You can combine `-f` with command-line targets.

## Data Sources

The tool queries free public APIs and tries them in order:

1. **[ipwho.is](https://ipwho.is)** (HTTPS), the primary provider
2. **[ip-api.com](https://ip-api.com)** (HTTP on the free tier), used as a fallback

Your own public IP (when no target is given) is discovered through `api.ipify.org`, with `ipwho.is` as a backup.

Local checks (validation, classification, reverse DNS) are done on your machine using Python's `ipaddress` and `socket` modules.

## Limitations

- **Geolocation is approximate.** It is usually accurate to country level, less so for city level, and it often points to the ISP's location rather than the actual user.
- **VPNs, proxies and mobile networks** can show a location far from the real device.
- **Rate limits:** free providers limit requests (`ip-api.com` allows roughly 45 per minute), so very large batches may fail partway.
- **Hostnames** resolve to the first address returned; other addresses for the same name are not looked up.
- The fallback provider's free tier uses **unencrypted HTTP**.
- Reverse DNS depends on the owner having configured a PTR record, so it is often missing.

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `not a valid IP address or resolvable hostname` | Check spelling, or your DNS/internet connection. |
| `All lookup providers failed` | No internet, a firewall blocking the APIs, or rate limiting. Wait and retry. |
| `Could not determine your public IP` | Check your connection, or pass an IP explicitly. |
| `Non-public address` note | Private, loopback and reserved addresses have no geolocation data. |
| Garbled colors on Windows | Use `--no-color` or Windows Terminal. |
| Slow lookups on large files | Reduce batch size to stay within provider rate limits. |

## Privacy & Disclaimer

Lookups send the queried IP address (or your own public IP in self-lookup mode) to third-party APIs. Do not use the tool for IPs you consider sensitive if that is a concern, and use `--offline` for local-only checks.

This tool is intended for network administration, troubleshooting, education and authorized security work. Geolocation data should not be used to identify, track or harass individuals. The author is not responsible for misuse.

## Author

**4rch-M4g**

Contributions, ideas and bug reports are welcome. Add a `LICENSE` file of your choice before publishing the project.
