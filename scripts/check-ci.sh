#!/usr/bin/env bash
# Run the GitHub Actions workflow locally, as faithfully as a shell can.
#
# Two failures got past hand-checking and cost a push cycle each: a step that
# only worked because the developer's .env existed, and an action tag that does
# not exist. This checks both.
#
#   scripts/check-ci.sh            everything
#   scripts/check-ci.sh --refs     only verify action refs resolve (needs network)
#   scripts/check-ci.sh --steps    only run the commands
#
# The root .env is moved aside for the duration: CI does not have one.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="${1:-all}"
hidden=""
if [ -f .env ]; then
  hidden="$(mktemp -t ai-workspace-env)"
  mv .env "$hidden"
fi
restore() { [ -n "$hidden" ] && mv "$hidden" .env && hidden=""; return 0; }
trap restore EXIT INT TERM

uv run --quiet --with pyyaml python - "$mode" <<'PY'
import os, pathlib, shutil, subprocess, sys, urllib.request, yaml

mode = sys.argv[1]
root = pathlib.Path.cwd()
workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
jobs = workflow["jobs"]
failures = []

def check_refs() -> None:
    print("\n\033[1maction refs\033[0m")
    seen = set()
    for name, job in jobs.items():
        for step in job["steps"]:
            ref = step.get("uses")
            if not ref or ref in seen:
                continue
            seen.add(ref)
            repo, _, tag = ref.partition("@")
            url = f"https://api.github.com/repos/{repo}/git/ref/tags/{tag}"
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    ok = response.status == 200
            except urllib.error.HTTPError as error:
                ok = False
            except Exception as error:  # offline: cannot judge, do not fail
                print(f"  ?    {ref} (could not check: {error})")
                continue
            print(f"  {'ok  ' if ok else 'FAIL'} {ref}")
            if not ok:
                failures.append(f"action ref {ref} does not resolve")

def run_steps() -> None:
    for name, job in jobs.items():
        workdir = root / job.get("defaults", {}).get("run", {}).get("working-directory", ".")
        env = {**os.environ, **{k: str(v) for k, v in (job.get("env") or {}).items()}}
        print(f"\n\033[1mjob {name}\033[0m  (cwd {workdir.relative_to(root)})")
        for step in job["steps"]:
            command = step.get("run")
            if not command:
                continue
            # A step may override the job's working directory or environment.
            cwd = root / step["working-directory"] if "working-directory" in step else workdir
            step_env = {**env, **{k: str(v) for k, v in (step.get("env") or {}).items()}}
            label = step.get("name") or command.strip().splitlines()[0]
            result = subprocess.run(
                command, shell=True, cwd=cwd, env=step_env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            if result.returncode == 0:
                print(f"  ok   {label}")
            else:
                print(f"  FAIL {label}")
                print("       " + "\n       ".join(result.stdout.strip().splitlines()[-6:]))
                failures.append(f"{name}: {label}")

if mode in ("all", "--refs"):
    check_refs()
if mode in ("all", "--steps"):
    run_steps()

print()
if failures:
    print(f"\033[31m{len(failures)} CI problem(s):\033[0m")
    for problem in failures:
        print(f"  - {problem}")
    sys.exit(1)
print("\033[32mCI would pass.\033[0m")
PY
status=$?
restore
exit $status
