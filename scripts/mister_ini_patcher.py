#!/usr/bin/env python3
"""
mister_ini_patcher.py

Keeps misteraddons/mister_ini product files in sync with upstream MiSTer.ini.
New/changed upstream settings are patched in; custom (non-default) product
settings are never overwritten.

Patch rules:
  - Upstream setting CHANGED  + product value == baseline value → update product
  - Upstream setting CHANGED  + product value != baseline value → skip (custom)
  - Upstream setting NEW (not in baseline)                      → append to product
  - Upstream setting REMOVED  + product value == baseline value → mark deprecated
  - Upstream setting REMOVED  + product value != baseline value → skip (custom)

Usage:
    python3 mister_ini_patcher.py [--dry-run] [--force] [--repo-dir PATH]
"""

import os, re, sys, json, subprocess, urllib.request, argparse
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

UPSTREAM_URL = (
    "https://raw.githubusercontent.com/MiSTer-devel/Main_MiSTer/master/MiSTer.ini"
)
COMMITS_API_URL = (
    "https://api.github.com/repos/MiSTer-devel/Main_MiSTer/commits"
    "?path=MiSTer.ini&per_page=1"
)
REPO_SSH_URL   = "git@github.com:misteraddons/mister_ini.git"
REPO_HTTPS_URL = "https://github.com/misteraddons/mister_ini.git"

# Relative to repo root
BASELINE_PATH = ".upstream_baseline.ini"
STATE_PATH    = ".upstream_state.json"

PRODUCT_INIS = [
    "Analog Video/RGB/MiSTer.ini",
    "Analog Video/S-Video and Composite/MiSTer.ini",
    "Analog Video/VGA/MiSTer.ini",
    "Analog Video/YPbPR (Component)/MiSTer.ini",
    "IO Direct/RGB/MiSTer.ini",
    "IO Direct/S-Video and Composite/MiSTer.ini",
    "IO Direct/VGA (WIP)/MiSTer.ini",
    "IO Direct/YPbPR (Component)/MiSTer.ini",
    "MiSTercade V1/15kHz/MiSTer.ini",
    "MiSTercade V1/31kHz/MiSTer.ini",
    "MiSTercade V2/15kHz/MiSTer.ini",
    "MiSTercade V2/31kHz/MiSTer.ini",
    "MiSTercade V2/31kHz (Upscaled)/MiSTer.ini",
    "MiSTercade V2/HDMI/MiSTer.ini",
]
LEGACY_PRODUCT_INIS = PRODUCT_INIS[:-1]

# ── Parsing ───────────────────────────────────────────────────────────────────

# Matches an active setting: key=value (optional trailing inline comment)
ACTIVE_RE = re.compile(r'^(\w+)\s*=\s*(.*?)(?:\s*;.*)?$')
# Matches a commented-out setting: ;key=value  or  ; key=value
COMMENTED_RE = re.compile(r'^;+\s*(\w+)\s*=\s*(.*?)(?:\s*;.*)?$')


def parse_ini(content: str) -> dict:
    """
    Parse MiSTer.ini content into:
      {key: {'value': str, 'commented': bool, 'line_idx': int}}

    Active settings take precedence over commented-out ones.
    First-occurrence wins among same-state duplicates.
    """
    settings: dict = {}
    for i, raw in enumerate(content.splitlines()):
        line = raw.strip()
        # Active setting
        if not line.startswith(';') and '=' in line and not line.startswith('['):
            m = ACTIVE_RE.match(line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                # Active overrides any previously seen commented entry
                if key not in settings or settings[key]['commented']:
                    settings[key] = {'value': val, 'commented': False, 'line_idx': i}
                continue
        # Commented setting
        if line.startswith(';'):
            m = COMMENTED_RE.match(line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if key not in settings:
                    settings[key] = {'value': val, 'commented': True, 'line_idx': i}
    return settings


# ── Patch logic ───────────────────────────────────────────────────────────────

def format_setting_line(key: str, val: str, commented: bool) -> str:
    """Format a setting line, preserving the ; prefix for commented settings."""
    if commented:
        return f";{key}={val}\n"
    return f"{key}={val}\n"


def patch_product_ini(
    product_path: Path,
    baseline: dict,
    upstream: dict,
    dry_run: bool = False,
    seed_missing_defaults: bool = False,
) -> list:
    """
    Apply upstream changes to a product INI file.
    Returns a list of change description strings.
    """
    content = product_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    product = parse_ini(content)

    changed_keys = {
        k for k, v in upstream.items()
        if k in baseline
        and (v['value'] != baseline[k]['value'] or v['commented'] != baseline[k]['commented'])
    }
    new_keys = set(upstream.keys()) - set(baseline.keys())
    removed_keys = set(baseline.keys()) - set(upstream.keys())

    changes = []
    modified_lines = list(lines)
    product_keys = set(product.keys())

    # ── Changed keys ──────────────────────────────────────────────────────────
    for key in changed_keys:
        if key not in product:
            continue
        prod = product[key]
        base = baseline[key]
        up   = upstream[key]

        if prod['value'] == base['value'] and prod['commented'] == base['commented']:
            # Product was tracking upstream default — safe to update
            idx = prod['line_idx']
            # Try to preserve any trailing comment/spacing from original line
            old = modified_lines[idx]
            new_line = format_setting_line(key, up['value'], up['commented'])
            # Keep trailing inline comment if present (e.g. "     ; set to 1 for ...")
            if not up['commented']:
                eq_pos = old.find('=')
                if eq_pos != -1:
                    after_eq = old[eq_pos + 1:].rstrip('\n')
                    old_val_len = len(base['value'])
                    trailing = after_eq[old_val_len:]
                    if trailing.strip().startswith(';') or trailing.startswith('     '):
                        new_line = f"{key}={up['value']}{trailing}\n"
            modified_lines[idx] = new_line

            action = (
                "uncomment" if (base['commented'] and not up['commented']) else
                "comment"   if (not base['commented'] and up['commented']) else
                "update"
            )
            changes.append(
                f"  [{action}] {key}: {base['value']!r} → {up['value']!r}"
            )
        else:
            # Product has a custom value — never touch it
            changes.append(
                f"  [skip/custom] {key}: product={prod['value']!r},"
                f" upstream changed to {up['value']!r}"
            )

    # ── New keys ──────────────────────────────────────────────────────────────
    new_lines_to_append = []
    date_str = datetime.now().strftime('%Y-%m-%d')
    for key in sorted(new_keys):
        if key in product:
            continue  # Already present for some reason
        up = upstream[key]
        new_lines_to_append.append(format_setting_line(key, up['value'], up['commented']))
        changes.append(f"  [new] {key}={up['value']!r}")

    if new_lines_to_append:
        header = f"\n; === New settings synced from upstream MiSTer.ini ({date_str}) ===\n"
        modified_lines.append(header)
        modified_lines.extend(new_lines_to_append)

    # ── Seed missing defaults for newly managed files ───────────────────────
    seeded_lines_to_append = []
    if seed_missing_defaults:
        for key, up in upstream.items():
            if key in product_keys:
                continue
            if key in new_keys:
                continue
            seeded_lines_to_append.append(
                format_setting_line(key, up['value'], up['commented'])
            )
            changes.append(f"  [seed] {key}={up['value']!r}")

    if seeded_lines_to_append:
        header = (
            f"\n; === Missing defaults synced for newly managed file ({date_str}) ===\n"
        )
        modified_lines.append(header)
        modified_lines.extend(seeded_lines_to_append)
    # ── Removed keys ─────────────────────────────────────────────────────────
    for key in removed_keys:
        if key not in product:
            continue
        prod = product[key]
        base = baseline[key]
        idx  = prod['line_idx']
        old  = modified_lines[idx]

        if prod['value'] == base['value'] and prod['commented'] == base['commented']:
            # Tracking upstream default — mark deprecated
            modified_lines[idx] = f"; [DEPRECATED upstream {date_str}] {old.lstrip()}"
            changes.append(f"  [deprecated] {key}")
        else:
            changes.append(f"  [skip/custom-removed] {key}: keeping custom value {prod['value']!r}")

    # ── Write back ────────────────────────────────────────────────────────────
    meaningful = [c for c in changes if '[skip' not in c]
    if meaningful and not dry_run:
        product_path.write_text(''.join(modified_lines), encoding='utf-8')

    return changes


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'mister-ini-patcher/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def run_git(args: list, cwd: Path) -> str:
    result = subprocess.run(
        ['git'] + args, cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync upstream MiSTer.ini changes to product INI files"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Print changes without writing or pushing"
    )
    parser.add_argument(
        '--force', action='store_true',
        help="Run even if upstream SHA is unchanged"
    )
    parser.add_argument(
        '--ci', action='store_true',
        help="CI mode: skip git clone/pull/push (repo already checked out, "
             "let the workflow handle commits)"
    )
    parser.add_argument(
        '--repo-dir',
        default=os.path.expanduser('~/Documents/Github/mister_ini'),
        help="Path to local mister_ini clone (will clone if missing; ignored in --ci mode)"
    )
    args = parser.parse_args()

    repo = Path(args.repo_dir) if not args.ci else Path('.')

    # ── Ensure repo exists locally (skipped in CI) ────────────────────────────
    if not args.ci:
        if not repo.exists():
            print(f"Cloning mister_ini to {repo} ...")
            try:
                subprocess.run(['git', 'clone', REPO_SSH_URL, str(repo)], check=True)
            except subprocess.CalledProcessError:
                print("SSH clone failed, trying HTTPS...")
                subprocess.run(['git', 'clone', REPO_HTTPS_URL, str(repo)], check=True)
        else:
            print(f"Updating local clone at {repo} ...")
            run_git(['pull', '--rebase'], repo)

    # ── Check upstream SHA ────────────────────────────────────────────────────
    print("Checking upstream MiSTer.ini for changes...")
    try:
        commits_data = json.loads(fetch_url(COMMITS_API_URL))
        upstream_sha = commits_data[0]['sha'] if commits_data else 'unknown'
    except Exception as e:
        print(f"Warning: could not fetch commit info ({e}). Proceeding anyway.")
        upstream_sha = 'unknown'

    state_file = repo / STATE_PATH
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    last_sha = state.get('last_upstream_sha', '')
    managed_product_inis = set(state.get('managed_product_inis', LEGACY_PRODUCT_INIS))
    newly_managed_files = [
        ini_rel for ini_rel in PRODUCT_INIS if ini_rel not in managed_product_inis
    ]

    if last_sha == upstream_sha and not args.force and upstream_sha != 'unknown' and not newly_managed_files:
        print(f"Upstream unchanged (SHA: {upstream_sha[:8]}). Nothing to do.")
        print("Use --force to run anyway.")
        return

    print(f"Upstream SHA: {last_sha[:8] or 'none'} → {upstream_sha[:8]}")
    if newly_managed_files:
        print("New managed product files detected:")
        for ini_rel in newly_managed_files:
            print(f"  {ini_rel}")

    # ── Fetch upstream content ────────────────────────────────────────────────
    print("Fetching upstream MiSTer.ini...")
    upstream_content = fetch_url(UPSTREAM_URL)
    upstream_parsed  = parse_ini(upstream_content)
    print(f"  Parsed {len(upstream_parsed)} settings from upstream.")

    # ── Load or bootstrap baseline ────────────────────────────────────────────
    baseline_file = repo / BASELINE_PATH

    if not baseline_file.exists():
        print("\nNo baseline found — bootstrapping from current upstream.")
        print("Product files will NOT be modified on first run.")
        print("Baseline is now established; changes will be tracked from here.\n")
        if not args.dry_run:
            baseline_file.write_text(upstream_content, encoding='utf-8')
            state['last_upstream_sha'] = upstream_sha
            state['last_run']          = datetime.now().isoformat()
            state_file.write_text(json.dumps(state, indent=2))
            run_git(['add', BASELINE_PATH, STATE_PATH], repo)
            run_git(['commit', '-m',
                     f'Bootstrap upstream MiSTer.ini baseline ({datetime.now().strftime("%Y-%m-%d")})'],
                    repo)
            run_git(['push'], repo)
            print("Baseline committed and pushed.")
        else:
            print("[DRY RUN] Baseline not written.")
        return

    baseline_content = baseline_file.read_text(encoding='utf-8')
    baseline_parsed  = parse_ini(baseline_content)
    print(f"  Baseline has {len(baseline_parsed)} settings.")

    # ── Apply patches ─────────────────────────────────────────────────────────
    all_changes: dict = {}
    files_modified: list = []

    for ini_rel in PRODUCT_INIS:
        ini_path = repo / ini_rel
        if not ini_path.exists():
            print(f"  WARNING: {ini_rel} not found — skipping")
            continue

        changes = patch_product_ini(
            ini_path, baseline_parsed, upstream_parsed, dry_run=args.dry_run,
            seed_missing_defaults=ini_rel in newly_managed_files,
        )
        meaningful = [c for c in changes if '[skip' not in c]
        all_changes[ini_rel] = changes
        if meaningful:
            files_modified.append(ini_rel)

    # ── Report ────────────────────────────────────────────────────────────────
    print()
    for ini_rel, changes in all_changes.items():
        meaningful = [c for c in changes if '[skip' not in c]
        if meaningful:
            print(f"✏️  {ini_rel}")
            for c in meaningful:
                print(c)
        else:
            skips = [c for c in changes if '[skip' in c]
            if skips:
                print(f"📌 {ini_rel} — {len(skips)} custom setting(s) preserved, no other changes")

    if not files_modified:
        print("No meaningful changes to apply across any product INI files.")

    if args.dry_run:
        print("\n[DRY RUN] No files written or pushed.")
        return

    # ── Update baseline + state ───────────────────────────────────────────────
    baseline_file.write_text(upstream_content, encoding='utf-8')
    state['last_upstream_sha'] = upstream_sha
    state['last_run']          = datetime.now().isoformat()
    state['managed_product_inis'] = PRODUCT_INIS
    state_file.write_text(json.dumps(state, indent=2))

    if args.ci:
        # In CI mode the workflow handles git add/commit/push.
        # Print a machine-readable summary for the workflow step.
        print(f"\nCI_FILES_MODIFIED={len(files_modified)}")
        if files_modified:
            print("Modified files:")
            for f in files_modified:
                print(f"  {f}")
        return

    # ── Commit + push (local mode only) ──────────────────────────────────────
    date_str    = datetime.now().strftime('%Y-%m-%d')
    stage_files = [BASELINE_PATH, STATE_PATH] + files_modified

    run_git(['add'] + stage_files, repo)
    porcelain = run_git(['status', '--porcelain'], repo)

    if porcelain:
        n = len(files_modified)
        msg = f"Sync upstream MiSTer.ini changes ({date_str})"
        if n:
            msg += f" — {n} file(s) updated"
        run_git(['commit', '-m', msg], repo)
        run_git(['push'], repo)
        print(f"\n✅ Pushed: {msg}")
    else:
        print("\nNothing to commit (all changes were skips).")


if __name__ == '__main__':
    main()
