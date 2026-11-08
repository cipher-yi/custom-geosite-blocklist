#!/bin/sh
# ==============================================================================
# Script: update-router.sh
# Description: Automated updater for custom geosite.dat on OpenWrt / ImmortalWrt
# Features:
#   - Dual-source failover: Primary jsDelivr CDN -> Fallback GitHub Releases
#   - Atomic lockfile & stale lock auto-recovery (5 min timeout)
#   - Size and Protobuf magic header verification (0x0a)
#   - Zero-downtime atomic replacement (mv)
#   - Background fork-and-detach execution with detailed logging
# ==============================================================================

# Target destination file on the router
DEST="${1:-/usr/share/v2ray/custom_geosite.dat}"

# Upstream repository settings
REPO="cipher-yi/custom-geosite-blocklist"
URL_JSDELIVR="https://cdn.jsdelivr.net/gh/${REPO}@release/geosite.dat"
URL_MIRROR="https://ghfast.top/https://github.com/${REPO}/releases/latest/download/geosite.dat"
URL_DIRECT="https://github.com/${REPO}/releases/latest/download/geosite.dat"

LOCK="/tmp/update-custom-geosite.lock"
LOG="/tmp/update-custom-geosite.log"

# Check existing lock file (auto-clear stale lock after 300s)
if [ -f "$LOCK" ]; then
    mtime=$(date -r "$LOCK" +%s 2>/dev/null || echo 0)
    age=$(( $(date +%s) - mtime ))
    if [ "$age" -lt 300 ]; then
        echo "Update already in progress (PID $(cat "$LOCK" 2>/dev/null), age ${age}s)" >&2
        exit 75
    fi
    rm -f "$LOCK"
fi

# Create atomic lock
if ! ( set -C; echo "$$" >"$LOCK" ) 2>/dev/null; then
    echo "Update already in progress" >&2
    exit 75
fi

# Spawn detached background worker
(
    exec >"$LOG" 2>&1
    trap 'rm -f "$LOCK"' EXIT INT TERM

    echo "=================================================="
    echo "$(date '+%F %T') [INFO] Starting GeoSite update"
    echo "$(date '+%F %T') [INFO] Destination: $DEST"
    echo "=================================================="

    TMP="${DEST}.new.$$"
    mkdir -p "$(dirname "$DEST")"
    download_success=0

    # Multi-tier failover: jsDelivr CDN -> GitHub Fast Mirror -> GitHub Direct
    for URL in "$URL_JSDELIVR" "$URL_MIRROR" "$URL_DIRECT"; do
        case "$URL" in
            *jsdelivr*) SOURCE_TYPE="jsDelivr CDN (Fast Primary)" ;;
            *ghfast*)   SOURCE_TYPE="GitHub Accelerator Mirror (Secondary)" ;;
            *)          SOURCE_TYPE="GitHub Releases Direct (Fallback)" ;;
        esac

        echo "$(date '+%F %T') [TRY] Fetching from $SOURCE_TYPE: $URL"

        if curl -fsSL --connect-timeout 15 --max-time 180 -o "$TMP" "$URL"; then
            size=$(wc -c < "$TMP" 2>/dev/null || echo 0)
            magic=$(hexdump -n 1 -e '1/1 "%02x"' "$TMP" 2>/dev/null)

            # Validate file size (> 1KB) and Protobuf magic header (0x0a)
            if [ "$size" -lt 1024 ]; then
                echo "$(date '+%F %T') [WARN] Verification failed: File too small ($size bytes)"
                rm -f "$TMP"
            elif [ "$magic" != "0a" ]; then
                echo "$(date '+%F %T') [WARN] Verification failed: Invalid Protobuf magic header (got '$magic', expected '0a')"
                rm -f "$TMP"
            else
                echo "$(date '+%F %T') [OK] Successfully verified payload from $SOURCE_TYPE ($size bytes)"
                download_success=1
                break
            fi
        else
            echo "$(date '+%F %T') [WARN] Curl download failed for $URL"
            rm -f "$TMP"
        fi
    done

    # Perform atomic replacement upon success
    if [ "$download_success" -eq 1 ]; then
        mv -f "$TMP" "$DEST"
        chmod 0644 "$DEST"
        echo "$(date '+%F %T') [SUCCESS] Installed updated GeoSite binary to $DEST"
        echo "$(date '+%F %T') [INFO] KixDNS file watcher will automatically hot-reload the changes"
        echo "$(date '+%F %T') ✓ Complete"
    else
        echo "$(date '+%F %T') [ERROR] All download attempts failed. Existing file retained"
        echo "$(date '+%F %T') ✗ Failed"
        rm -f "$TMP"
        exit 1
    fi
) </dev/null >/dev/null 2>&1 &

echo "Update process started in background. Monitor via: cat $LOG"
exit 0
