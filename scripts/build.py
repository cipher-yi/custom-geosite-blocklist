#!/usr/bin/env python3
"""
Custom GeoSite Blocklist Builder
Aggregates, sanitizes, deduplicates, and formats multi-source DNS blocklists
into standard V2Ray/Xray GeoSite data files.
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error
import yaml

# Domain validation regex (RFC compliant domain format)
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

# Common IPv4 check regex to exclude raw IPs
IPV4_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def sanitize_line(raw_line: str) -> str | None:
    """
    Parse and extract a clean domain name from multiple filter syntax variations:
    - Pure domain: example.com
    - AdBlock style: ||example.com^
    - Hosts style: 0.0.0.0 example.com / 127.0.0.1 example.com
    - Surge / QuantumultX style: HOST-SUFFIX,example.com,REJECT
    """
    line = raw_line.strip()
    if not line or line.startswith(("#", "!", ";", "//", "[")):
        return None

    # Handle QuantumultX / Surge rule syntax (HOST,domain.com,REJECT)
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0].upper() in ("HOST", "HOST-SUFFIX", "DOMAIN", "DOMAIN-SUFFIX"):
            line = parts[1]

    # Handle AdBlock rule syntax (||example.com^)
    if line.startswith("||"):
        line = line[2:]
    if "^" in line:
        line = line.split("^")[0]

    # Handle Hosts rule syntax (0.0.0.0 example.com or 127.0.0.1 example.com)
    tokens = line.split()
    domain = tokens[-1] if len(tokens) > 1 else tokens[0]

    # Normalize case and strip trailing dots
    domain = domain.lower().rstrip(".")

    # Exclude wildcard prefixes (*.example.com -> example.com)
    if domain.startswith("*."):
        domain = domain[2:]

    # Validate against regex and ignore pure IPs
    if DOMAIN_REGEX.match(domain) and not IPV4_REGEX.match(domain):
        return domain

    return None


def prune_subdomains(domains: set[str]) -> set[str]:
    """
    Remove redundant subdomains if their parent domain is already present.
    GeoSite rules default to subdomain matching, so keeping only apex/parent
    drastically reduces file size and memory footprint without losing coverage.
    """
    sorted_domains = sorted(domains, key=lambda d: (d.count("."), len(d)))
    pruned = set()
    for d in sorted_domains:
        parts = d.split(".")
        redundant = False
        for i in range(1, len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in pruned:
                redundant = True
                break
        if not redundant:
            pruned.add(d)
    return pruned


def fetch_url_with_retry(url: str, retries: int = 3, timeout: int = 25) -> str | None:
    """
    Download file content over HTTP/HTTPS with automatic retries and custom User-Agent.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"    [WARN] Attempt {attempt}/{retries} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(2)
    return None


def load_whitelist(whitelist_path: str) -> set[str]:
    """
    Load user-defined whitelist domains.
    """
    whitelist = set()
    if os.path.exists(whitelist_path):
        with open(whitelist_path, "r", encoding="utf-8") as f:
            for line in f:
                domain = sanitize_line(line)
                if domain:
                    whitelist.add(domain)
        print(f"[*] Loaded {len(whitelist)} whitelist entries from {whitelist_path}")
    return whitelist


def is_whitelisted(domain: str, whitelist: set[str]) -> bool:
    """
    Check if a domain or its parent suffix matches the whitelist.
    """
    if domain in whitelist:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        parent_domain = ".".join(parts[i:])
        if parent_domain in whitelist:
            return True
    return False


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    config_file = os.path.join(base_dir, "config.yaml")
    whitelist_file = os.path.join(base_dir, "whitelist.txt")
    data_dir = os.path.join(project_root, "data")

    if not os.path.exists(config_file):
        print(f"[ERROR] Config file not found: {config_file}")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    whitelist = load_whitelist(whitelist_file)
    os.makedirs(data_dir, exist_ok=True)

    sources = config.get("sources", {})
    all_combined_domains: set[str] = set()

    for tag, conf in sources.items():
        print(f"\n[+] Processing tag: '{tag}'")
        tag_domains: set[str] = set()

        # 1. Process local static rules
        local_rules = conf.get("local_rules", [])
        for item in local_rules:
            dom = sanitize_line(item)
            if dom and not is_whitelisted(dom, whitelist):
                tag_domains.add(dom)
        if local_rules:
            print(f"  - Loaded {len(local_rules)} static local rules")

        # 2. Process remote URLs
        remotes = conf.get("remotes", [])
        for remote in remotes:
            name = remote.get("name", "unnamed")
            url = remote.get("url")
            if not url:
                continue

            print(f"  - Fetching remote '{name}': {url}")
            content = fetch_url_with_retry(url)
            if not content:
                print(f"    [FAIL] Skipping source '{name}' due to download failure.")
                continue

            added = 0
            for line in content.splitlines():
                dom = sanitize_line(line)
                if dom and not is_whitelisted(dom, whitelist):
                    tag_domains.add(dom)
                    added += 1
            print(f"    -> Extracted {added} valid domains from '{name}'")

        pruned_domains = prune_subdomains(tag_domains)
        print(f"  [SUMMARY] Domains for tag '{tag}': {len(tag_domains)} -> {len(pruned_domains)} after pruning")

        # Write tag file in V2Ray domain-list-community format
        tag_output_file = os.path.join(data_dir, tag)
        with open(tag_output_file, "w", encoding="utf-8") as out:
            for domain in sorted(pruned_domains):
                out.write(f"{domain}\n")

    print(f"\n==========================================")
    print(f"[*] Successfully generated GeoSite data files in: {data_dir}")
    print(f"[*] Omitted redundant 'block-all' tag to keep binary under 20MB for jsDelivr CDN")
    print(f"==========================================")


if __name__ == "__main__":
    main()
