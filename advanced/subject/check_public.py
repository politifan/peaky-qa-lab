import json,sys,subprocess,shutil,tempfile,os
import xml.etree.ElementTree as ET
from pathlib import Path
folder=Path(__file__).resolve().parent
key=sys.argv[1];tasks=json.loads((folder/'tasks.json').read_text(encoding='utf-8'))
task=tasks[key];source=folder/'submissions'/(key+'.py')
if task['kind']=='locust':
    print('Start the stand in a separate terminal: python -m uvicorn run_app:app --port 8765')
    raise SystemExit(subprocess.run([sys.executable,'-m','locust','-f',str(source),'--headless','-u','2','-r','2','-t','5s','--host','http://127.0.0.1:8765','--exit-code-on-error','1']).returncode)
copy=folder/('test_'+key.replace('-','_')+'.py');shutil.copyfile(source,copy)
environment=os.environ.copy();environment['PEAKY_QA_VARIANT']='good'
try:
 with tempfile.TemporaryDirectory(prefix='peaky-public-') as directory:
  report=Path(directory)/'junit.xml'
  result=subprocess.run([sys.executable,'-m','pytest',str(copy),'-q','--junitxml='+str(report)],env=environment,timeout=120)
  if result.returncode:raise SystemExit(result.returncode)
  cases=list(ET.parse(report).getroot().iter('testcase'))
  if len(cases)<task['min_tests'] or any(c.find('skipped') is not None or c.find('error') is not None for c in cases):raise SystemExit('Required non-skipped tests were not executed.')
  print('Good baseline passed; sensitivity requires the separate good/bad check.')
finally:copy.unlink(missing_ok=True)
