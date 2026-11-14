#!/usr/bin/env python3
import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

base = sys.argv[1]
changed = subprocess.check_output(["git", "diff", "--name-only", f"{base}...HEAD"], text=True).splitlines()
sources = [pathlib.Path(name) for name in changed if name.startswith("modules/") and name.endswith("/source.json")]
if not sources:
    print("PASS: no reviewed source.json changed; unrelated registry update")
    raise SystemExit(0)
for path in sources:
    source = json.loads(path.read_text())
    url = source["url"]
    integrity = source["integrity"]
    if not url.startswith("https://") or not integrity.startswith("sha256-"):
        raise SystemExit(f"unsupported reviewed source: {path}")
    expected = base64.b64decode(integrity.removeprefix("sha256-")).hex()
    request = urllib.request.Request(url, headers={"User-Agent": "bcr-controlled-validation"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected:
        raise SystemExit(f"reviewed source mismatch for {path}: {observed} != {expected}")
    print(f"PASS reviewed source {path}: {observed}")
