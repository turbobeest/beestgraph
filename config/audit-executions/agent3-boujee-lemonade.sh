#!/bin/bash
STATUS="/home/turbobeest/beestgraph/config/audit-executions/agent3-boujee-lemonade.json"
AUDIT="/home/turbobeest/beestgraph/config/audit-recommendations.json"
PROMPT="/home/turbobeest/beestgraph/config/audit-executions/agent3-boujee-lemonade.prompt"
CLAUDE="/home/turbobeest/.local/bin/claude"
OUTPUT="/home/turbobeest/beestgraph/config/audit-executions/agent3-boujee-lemonade.output"
REC_ID="agent3-boujee-lemonade"
VAULT="/home/turbobeest/vault"
FINISHER="/home/turbobeest/beestgraph/config/audit-executions/finisher.py"

update_step() {
  python3 -c "import json,sys; f=sys.argv[1]; d=json.load(open(f)); d['steps'].append(sys.argv[2]); json.dump(d,open(f,'w'),indent=2)" "$STATUS" "$1"
}

update_step "Starting Claude Code session..."

cd "$VAULT"
$CLAUDE --print "$(cat $PROMPT)" --output-format json --permission-mode acceptEdits --add-dir "$VAULT" > "$OUTPUT" 2>&1
EC=$?

python3 "$FINISHER" "$STATUS" "$AUDIT" "$REC_ID" "$EC"
