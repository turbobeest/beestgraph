import json, sys
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
