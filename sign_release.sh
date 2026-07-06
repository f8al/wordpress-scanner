#!/usr/bin/env bash
#
# sign_release.sh — regenerate and DSA-sign version.sig for the auto-update mechanism.
#
# The extension (burp_wp.py -> update_burp_wp / verify_update_message) fetches
# version.sig from this fork, verifies its SHA256withDSA signature against the
# public key embedded in verify_update_message(), then downloads `url` and checks
# its sha256. This script rebuilds version.sig so all of that lines up.
#
# Run it after every change to burp_wp.py that you intend to ship, because the
# sha256 in version.sig must match the exact burp_wp.py served from master.
#
# Requirements: the private key (version_signing_key.pem, gitignored) whose public
# half is embedded in verify_update_message(). Guard that file — it is the only
# thing that can produce a version.sig this build will accept.
#
# Usage:
#   ./sign_release.sh ["changelog text"]
#
# The version number is read from BURP_WP_VERSION in burp_wp.py automatically.
# If no changelog is given, a default referencing the version is used.

set -euo pipefail

cd "$(dirname "$0")"

KEY="version_signing_key.pem"
SRC="burp_wp.py"
OUT="version.sig"
REPO_RAW="https://raw.githubusercontent.com/f8al/wordpress-scanner/master"

[ -f "$KEY" ] || { echo "error: $KEY not found — cannot sign without the private key" >&2; exit 1; }
[ -f "$SRC" ] || { echo "error: $SRC not found" >&2; exit 1; }

VERSION="$(grep -E "^BURP_WP_VERSION *= *'" "$SRC" | head -1 | sed -E "s/.*'([^']+)'.*/\1/")"
[ -n "$VERSION" ] || { echo "error: could not read BURP_WP_VERSION from $SRC" >&2; exit 1; }

CHANGELOG="${1:-${VERSION}: see repository for details}"
HASH="$(sha256sum "$SRC" | cut -d' ' -f1)"
URL="${REPO_RAW}/${SRC}"

# The message is a single JSON line. json.loads() is order-insensitive, but the
# signature covers these exact bytes, so build it deterministically here.
MSG="{\"version_number\": \"${VERSION}\", \"url\": \"${URL}\", \"sha256\": \"${HASH}\", \"changelog\": \"${CHANGELOG}\"}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

printf '%s' "$MSG" > "$TMP/msg.txt"
# SHA256withDSA — openssl emits a DER-encoded (r,s) signature, the same format
# Java's Signature.verify() expects.
openssl dgst -sha256 -sign "$KEY" -out "$TMP/sig.bin" "$TMP/msg.txt"
SIG="$(base64 -w0 "$TMP/sig.bin")"

# version.sig = message line + signature line, NO trailing newline
# (verify_update_message splits on "\n" and expects exactly 2 parts).
printf '%s\n%s' "$MSG" "$SIG" > "$OUT"

# Self-check: verify with the public half of the key before we trust the output.
openssl dsa -in "$KEY" -pubout -out "$TMP/pub.pem" 2>/dev/null
if openssl dgst -sha256 -verify "$TMP/pub.pem" -signature "$TMP/sig.bin" "$TMP/msg.txt" >/dev/null 2>&1; then
    echo "signed $OUT for version $VERSION"
    echo "  sha256(${SRC}) = $HASH"
    echo "  signature verified OK"
else
    echo "error: signature failed self-verification — $OUT may be invalid" >&2
    exit 1
fi
