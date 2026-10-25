from pathlib import Path
import json,sys
mode=sys.argv[1] if len(sys.argv)>1 else 'none'
if mode not in ['none','validation','retry','storage','isolation']:
    raise SystemExit('Use none, validation, retry, storage or isolation')
Path(__file__).with_name('fault.json').write_text(json.dumps({'mode':mode}),encoding='utf-8')
print('mode='+mode+'; restart the application before testing')
