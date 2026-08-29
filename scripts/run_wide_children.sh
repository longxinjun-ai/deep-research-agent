#!/usr/bin/env bash
# Batch runner skeleton for wide research with external agent CLIs
# (codex / claude / opencode ...). The Python implementation in
# deep_research_agent/wide.py covers the same protocol without a CLI
# dependency; keep this script for CLI-based workflows.
#
# Usage: ./run_wide_children.sh <manifest.json> <child_prompt_template.md>
set -euo pipefail

MANIFEST="${1:?usage: run_wide_children.sh <manifest.json> <prompt_template.md>}"
TEMPLATE="${2:?usage: run_wide_children.sh <manifest.json> <prompt_template.md>}"
CONCURRENCY="${CONCURRENCY:-8}"
TIMEOUT_SECS="${TIMEOUT_SECS:-600}"
OUT_DIR="${OUT_DIR:-child_outputs}"
LOG_DIR="${LOG_DIR:-logs}"
# Which agent CLI to drive: codex | claude | none (python fallback)
RUNNER="${RUNNER:-none}"

mkdir -p "$OUT_DIR" "$LOG_DIR"

run_child() {
  local id="$1" prompt_file="$2" output="$OUT_DIR/$1.md" log="$LOG_DIR/$1.log"
  # idempotent: skip children whose output already exists and is non-trivial
  if [[ -s "$output" ]]; then echo "skip $id (cached)"; return 0; fi
  case "$RUNNER" in
    codex)
      timeout "$TIMEOUT_SECS" codex exec \
        --sandbox workspace-write \
        -c model_reasoning_effort="low" \
        --output-last-message "$output" \
        - <"$prompt_file" 2>&1 | tee "$log" >/dev/null || echo "$id failed" >>"$LOG_DIR/failed_ids"
      ;;
    *)
      echo "set RUNNER=codex (or wire your own CLI here); see wide.py for the pure-Python path" | tee "$log"
      ;;
  esac
}

# dispatch with bounded concurrency; prompts rendered from the template with
# python to avoid heredoc/quoting pitfalls when injecting manifest fields
python3 - "$MANIFEST" "$TEMPLATE" <<'PY' > /tmp/wide_jobs.tsv
import json, sys
manifest = json.load(open(sys.argv[1]))
tpl = open(sys.argv[2]).read()
for st in manifest["subtasks"]:
    sid = st["id"]
    prompt = tpl.replace("{{id}}", sid).replace("{{title}}", st["title"]) \
                .replace("{{instruction}}", st.get("instruction", "")) \
                .replace("{{queries}}", "\n".join(st.get("suggested_queries", [])))
    path = f"prompts/{sid}.md"
    import os; os.makedirs("prompts", exist_ok=True)
    open(path, "w").write(prompt)
    print(f"{sid}\t{path}")
PY

mkdir -p prompts
while IFS=$'\t' read -r id prompt_file; do
  run_child "$id" "$prompt_file" &
  while (("$(jobs -r | wc -l)" >= CONCURRENCY)); do wait -n; done
done < /tmp/wide_jobs.tsv
wait

# coverage check
python3 - "$MANIFEST" "$OUT_DIR" <<'PY'
import json, sys, pathlib
manifest = json.load(open(sys.argv[1]))
outdir = pathlib.Path(sys.argv[2])
missing = [s["id"] for s in manifest["subtasks"] if not (outdir / f"{s['id']}.md").stat().st_size > 0]
print("missing:", missing if missing else "none")
PY
