import json,sys,subprocess,shutil
from pathlib import Path
folder=Path(__file__).resolve().parent
key=sys.argv[1];tasks=json.loads((folder/'tasks.json').read_text(encoding='utf-8'))
task=tasks[key];source=folder/'submissions'/(key+'.py')
if task['kind']=='locust':
    print('Start the stand in a separate terminal: python -m uvicorn run_app:app --port 8765')
    raise SystemExit(subprocess.run([sys.executable,'-m','locust','-f',str(source),'--headless','-u','2','-r','2','-t','5s','--host','http://127.0.0.1:8765','--exit-code-on-error','1']).returncode)
copy=folder/('test_'+key.replace('-','_')+'.py');shutil.copyfile(source,copy)
try:raise SystemExit(subprocess.run([sys.executable,'-m','pytest',str(copy),'-q']).returncode)
finally:copy.unlink(missing_ok=True)
