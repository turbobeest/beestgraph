import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const CONFIG_DIR = path.join(
  process.env.HOME ?? "/home/turbobeest",
  "beestgraph",
  "config",
);
const AUDIT_PATH = path.join(CONFIG_DIR, "audit-recommendations.json");
const EXEC_DIR = path.join(CONFIG_DIR, "audit-executions");

interface StatusFile {
  id: string;
  state: "running" | "complete" | "error";
  steps: string[];
  started: string;
  finished?: string;
  error?: string;
}

// GET /api/audit/execute?id=xxx — poll execution status
export async function GET(request: NextRequest): Promise<NextResponse> {
  const id = request.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 });
  }

  const statusPath = path.join(EXEC_DIR, `${id}.json`);
  if (!fs.existsSync(statusPath)) {
    return NextResponse.json({ state: "not_found" });
  }

  try {
    const raw = fs.readFileSync(statusPath, "utf-8");
    return NextResponse.json(JSON.parse(raw));
  } catch {
    return NextResponse.json({ state: "error", error: "Failed to read status" });
  }
}

// POST /api/audit/execute — start execution for a recommendation
export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = await request.json() as { id: string };
  const { id } = body;

  if (!id) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 });
  }

  // Check if already running
  const statusPath = path.join(EXEC_DIR, `${id}.json`);
  if (fs.existsSync(statusPath)) {
    try {
      const existing: StatusFile = JSON.parse(fs.readFileSync(statusPath, "utf-8"));
      if (existing.state === "running") {
        return NextResponse.json({ error: "Already running", state: "running" }, { status: 409 });
      }
    } catch { /* proceed */ }
  }

  // Read recommendation
  let rec;
  try {
    const audit = JSON.parse(fs.readFileSync(AUDIT_PATH, "utf-8"));
    rec = audit.recommendations.find((r: { id: string }) => r.id === id);
  } catch {
    return NextResponse.json({ error: "Failed to read audit data" }, { status: 500 });
  }

  if (!rec) {
    return NextResponse.json({ error: "Recommendation not found" }, { status: 404 });
  }

  // Write initial status
  const status: StatusFile = {
    id,
    state: "running",
    steps: ["Initializing Claude Code..."],
    started: new Date().toISOString(),
  };
  fs.writeFileSync(statusPath, JSON.stringify(status, null, 2));

  // Build the prompt for Claude Code
  const prompt = buildPrompt(rec);

  // Spawn Claude Code in the background
  const scriptPath = path.join(CONFIG_DIR, "audit-executions", `${id}.sh`);
  const claudePath = path.join(process.env.HOME ?? "/home/turbobeest", ".local", "bin", "claude");

  // Write prompt to file so shell script can read it
  const promptPath = path.join(EXEC_DIR, id + ".prompt");
  fs.writeFileSync(promptPath, prompt, "utf-8");

  // Build script using string concatenation to avoid template literal issues
  const lines = [
    "#!/bin/bash",
    "STATUS=" + JSON.stringify(statusPath),
    "AUDIT=" + JSON.stringify(AUDIT_PATH),
    "PROMPT=" + JSON.stringify(promptPath),
    "CLAUDE=" + JSON.stringify(claudePath),
    "OUTPUT=" + JSON.stringify(path.join(EXEC_DIR, id + ".output")),
    "REC_ID=" + JSON.stringify(id),
    "VAULT=" + JSON.stringify(path.join(process.env.HOME ?? "/home/turbobeest", "vault")),
    "FINISHER=" + JSON.stringify(path.join(EXEC_DIR, "finisher.py")),
    "",
    'update_step() {',
    '  python3 -c "import json,sys; f=sys.argv[1]; d=json.load(open(f)); d[\'steps\'].append(sys.argv[2]); json.dump(d,open(f,\'w\'),indent=2)" "$STATUS" "$1"',
    '}',
    "",
    'update_step "Starting Claude Code session..."',
    "",
    'cd "$VAULT"',
    '$CLAUDE --print "$(cat $PROMPT)" --output-format json --permission-mode acceptEdits --add-dir "$VAULT" > "$OUTPUT" 2>&1',
    "EC=$?",
    "",
    'python3 "$FINISHER" "$STATUS" "$AUDIT" "$REC_ID" "$EC"',
  ];
  const script = lines.join("\n") + "\n";

  fs.writeFileSync(scriptPath, script, { mode: 0o755 });

  // Write finisher.py (idempotent)
  const finisherPath = path.join(EXEC_DIR, "finisher.py");
  if (!fs.existsSync(finisherPath)) {
    fs.writeFileSync(finisherPath, `import json, sys
from datetime import datetime

status_file = sys.argv[1]
audit_file = sys.argv[2]
rec_id = sys.argv[3]
exit_code = int(sys.argv[4])
finished = datetime.now().astimezone().isoformat()

d = json.load(open(status_file))
if exit_code == 0:
    d['state'] = 'complete'
    d['steps'].append('Claude Code session complete.')
else:
    d['state'] = 'error'
    d['steps'].append(f'Claude Code exited with code {exit_code}')
    d['error'] = f'Exit code {exit_code}'
d['finished'] = finished
json.dump(d, open(status_file, 'w'), indent=2)

if exit_code == 0:
    a = json.load(open(audit_file))
    for r in a['recommendations']:
        if r['id'] == rec_id:
            r['status'] = 'approved'
            break
    json.dump(a, open(audit_file, 'w'), indent=2)
`);
  }

  // Spawn detached
  const child = spawn("bash", [scriptPath], {
    detached: true,
    stdio: "ignore",
    env: { ...process.env, HOME: process.env.HOME ?? "/home/turbobeest" },
  });
  child.unref();

  return NextResponse.json({ started: true, id, pid: child.pid });
}

function buildPrompt(rec: Record<string, unknown>): string {
  const cat = rec.categorization as Record<string, Record<string, string>> | undefined;
  const interlinks = (rec.interlinking as string[]) || [];

  let prompt = `You are applying an approved audit recommendation to a beestgraph vault file.

## File
${rec.file}

## Title
${rec.title}

## Recommendation Summary

### Intent Assessment
${rec.intent}

### Categorization Changes`;

  if (cat) {
    for (const [key, val] of Object.entries(cat)) {
      if (val.recommended && val.recommended !== "no change" && val.recommended !== "not applicable" && val.current !== val.recommended) {
        prompt += `\n- **${key.toUpperCase()}**: "${val.current}" → "${val.recommended}" (${val.justification})`;
      }
    }
  }

  prompt += `

### Metadata Issues
${rec.metadata}

### Suggested Interlinks
${interlinks.length > 0 ? interlinks.map(l => `- [[${l}]]`).join("\n") : "None"}

### Enrichment
${rec.enrichment}

## Instructions
1. Read the file at the path above
2. Apply all recommended categorization changes to the frontmatter
3. Fix any metadata issues described above (add missing fields, correct formats)
4. Add any missing interlinks to the Related/Connections section
5. Do NOT add enrichment content directly — only fix metadata and links
6. Do NOT change the body content unless specifically noted in metadata issues
7. Write the updated file back

Important: Use the beestgraph frontmatter standard:
- uid, title, type, tags, status (published/draft/qualifying), content_stage (fleeting/literature/evergreen/reference)
- topics (YAML array of topic slugs), dates: { created, modified }, para, version
- Remove legacy fields: aliases, project, updated, created (flat), content_type, quality, recommended_*

After making changes, briefly state what you changed.`;

  return prompt;
}
