# Custom GeoSite Blocklist

[![Build and Release GeoSite Blocklist](https://github.com/cipher-yi/custom-geosite-blocklist/actions/workflows/build.yml/badge.svg)](https://github.com/cipher-yi/custom-geosite-blocklist/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An automated, unadulterated, and high-performance **GeoSite** binary blocklist compiled specifically for **KixDNS**, **V2Ray**, **Xray**, **sing-box**, and **Clash/Mihomo**.

This project provides modular, transparent, and multi-category DNS-level protection without political bias, stealth censorship, or arbitrary opinion injection.

---

## 🎯 Highlights & Features

* **🛡️ Zero Ideological Bias**: Completely free from hidden political or religious censorship lists that plague some conventional blocklists (e.g. `anti-AD`). We only filter verifiable ads, trackers, malware, and surveillance endpoints.
* **🧩 Modular Tag Hierarchy**: Multiple distinct tags are built into a single `geosite.dat` file. You can cherry-pick individual tags or block everything in one rule.
* **🇨🇳 Comprehensive China Defense**: Built-in rules targeting China-specific privacy violations, including National Anti-Fraud platform probes, Antiy AVL cloud scanners, smartphone installer surveillance (MIUI, ColorOS, OriginOS, HarmonyOS), commercial device fingerprinters (Tongdun, Shumei), and HTTPDNS bypasses.
* **🚀 Native Radix Trie Performance**: Compiled into binary Radix Trie format via official `v2fly` compilers for microsecond matching latencies with minimal RAM usage.
* **⚡ Daily Automated Cloud Builds**: GitHub Actions automatically pulls, sanitizes, deduplicates, verifies, and publishes updated binaries every day.

---

## 📦 GeoSite Categories (Tags)

| GeoSite Tag | Description & Coverage |
| :--- | :--- |
| `geosite:antifraud` | **China Specific**: National Anti-Fraud app probes, Antiy AVL cloud virus inspection, Xiaomi / Huawei / OPPO / vivo installation censorship, device fingerprinting (Shumei / Tongdun / Dingxiang), and ISP anti-fraud redirection pages. |
| `geosite:malware` | **Global Threat Intel**: Active malware delivery servers, ransomware C2 nodes, credential harvesters, and phishing domains (via HaGeZi TIF & URLHaus). |
| `geosite:pcdn` | **Anti-PCDN Leeching**: Domestic video streaming services (iQiyi, Youku, Tencent Video, Baidu Wangpan) leeching residential home upload bandwidth. |
| `geosite:httpdns` | **Anti-HTTPDNS Bypass**: Blocks major domestic HTTPDNS endpoints (Tencent, Alibaba, ByteDance, NetEase) to force mobile apps back to local DNS inspection. |
| `geosite:privacy` | **Global & Domestic Telemetry**: Device diagnostic loggers, usage analytics, crash reporting SDKs, and behavioral trackers (Apple, Windows, Xiaomi, Huawei, etc.). |
| `geosite:ads` | **Commercial Advertisements**: Clean commercial popups, banners, app splash screens, and tracking networks without breaking websites. |
| `geosite:doh_bypass` | **Anti-Bypass**: Public Encrypted DNS (DoH/DoT) endpoints to prevent clients from surreptitiously bypassing router DNS enforcement. |
| `geosite:block-all` | **Master Aggregation**: Combines all blocking categories (`antifraud`, `malware`, `pcdn`, `httpdns`, `privacy`, `ads`) into a single tag. |

---

## 📥 Direct Download Links

* **Latest Release:** `https://github.com/cipher-yi/custom-geosite-blocklist/releases/latest/download/geosite.dat`
* **Fast jsDelivr CDN:** `https://cdn.jsdelivr.net/gh/cipher-yi/custom-geosite-blocklist@release/geosite.dat`
* **SHA256 Checksum:** `https://github.com/cipher-yi/custom-geosite-blocklist/releases/latest/download/geosite.dat.sha256sum`

---

## 🛠️ Usage Examples

### 1. KixDNS (OpenWrt / ImmortalWrt)

In your `/etc/kixdns/pipeline.json`:

```json
{
  "settings": {
    "geosite_data_paths": [
      "/usr/share/v2ray/geosite.dat",
      "/etc/kixdns/custom_geosite.dat"
    ]
  },
  "pipeline_select": [
    {
      "comment": "Block Anti-Fraud, Telemetry & PCDN",
      "pipeline": "block",
      "matchers": [
        { "type": "geo_site", "value": "antifraud" },
        { "type": "geo_site", "value": "privacy", "operator": "or" },
        { "type": "geo_site", "value": "pcdn", "operator": "or" }
      ]
    }
  ]
}
```

> **Tip**: KixDNS features an active file watcher. Whenever `/etc/kixdns/custom_geosite.dat` is downloaded and replaced, KixDNS immediately hot-reloads with zero downtime.

---

### 2. V2Ray / Xray

In your `config.json`:

```json
{
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "outboundTag": "block",
        "domain": [
          "geosite:antifraud",
          "geosite:privacy",
          "geosite:pcdn",
          "geosite:ads"
        ]
      }
    ]
  }
}
```

---

### 3. Mihomo / Clash.Meta

In your `config.yaml`:

```yaml
geodata-mode: true
geox-url:
  geosite: "https://github.com/cipher-yi/custom-geosite-blocklist/releases/latest/download/geosite.dat"

rules:
  - GEOSITE,antifraud,REJECT
  - GEOSITE,privacy,REJECT
  - GEOSITE,pcdn,REJECT
  - GEOSITE,ads,REJECT
```

---

## ⏰ Automated Router Updates (Cron)

On your OpenWrt/ImmortalWrt router, add a cron job via `crontab -e` to fetch updates every Monday at 04:00 AM:

```bash
0 4 * * 1 curl -fsSL https://github.com/cipher-yi/custom-geosite-blocklist/releases/latest/download/geosite.dat -o /etc/kixdns/custom_geosite.dat
```

---

## ⚙️ Customization & Whitelist

1. **Add Custom Upstreams**: Edit [`scripts/config.yaml`](scripts/config.yaml) to add or remove remote filter lists.
2. **Whitelist Domains**: Add any falsely flagged domains to [`scripts/whitelist.txt`](scripts/whitelist.txt) (one domain per line).

---

## 📜 Credits & Acknowledgments

* [HaGeZi's DNS Blocklists](https://github.com/hagezi/dns-blocklists) - Industry-standard transparent threat intelligence and trackers.
* [Cats-Team/AdRules](https://github.com/Cats-Team/AdRules) - China-specific HTTPDNS and PCDN detection.
* [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) - Granular privacy categorization.
* [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) - GeoSite compiler engine.

---

## 📄 License

Licensed under the [MIT License](LICENSE).
