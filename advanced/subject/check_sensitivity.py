"""Run the same learner tests against good and one declared defect. No server grading."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,tempfile,uuid
import xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
VARIANTS=('quantity','schema','duplicate','volatile','tenant_leak','ui_false_success','shared','factory_alias','dependency_status','dependency_schema','ci_skip','junit_ignores_errors')
def run(task,variant,work):
    source=ROOT/'submissions'/(task['key']+'.py')
    xml=work/(variant+'.xml');environment=os.environ.copy();environment['PEAKY_QA_VARIANT']=variant
    result=subprocess.run([sys.executable,'-m','pytest',str(source),'-q','--junitxml='+str(xml)],cwd=ROOT,env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    if not xml.exists():raise RuntimeError('No JUnit report: '+result.stderr[-1200:])
    cases=list(ET.parse(xml).getroot().iter('testcase'));errors=sum(c.find('error') is not None for c in cases);skips=sum(c.find('skipped') is not None for c in cases)
    failures=[c.find('failure') for c in cases if c.find('failure') is not None]
    assertions=sum('AssertionError' in (f.get('message','')+' '+(f.text or '')) or 'assert ' in (f.text or '') for f in failures)
    return dict(variant=variant,exit=result.returncode,collected=len(cases),errors=errors,skipped=skips,failures=len(failures),assertion_failures=assertions,output=result.stdout[-6000:]+result.stderr[-1000:])
def main():
    p=argparse.ArgumentParser();p.add_argument('key');p.add_argument('--variant',required=True,choices=VARIANTS);args=p.parse_args()
    tasks=json.loads((ROOT/'tasks.json').read_text(encoding='utf-8'));task=tasks[args.key]
    if task['kind']=='locust':raise SystemExit('Locust needs the separate measured good/bad server route described in OPEN-MUTATIONS.txt.')
    source=ROOT/'submissions'/(args.key+'.py')
    if not source.exists():raise SystemExit('Create your submission first: '+str(source))
    with tempfile.TemporaryDirectory(prefix='peaky-qa-sensitivity-') as directory:
        work=pathlib.Path(directory);good=run(task,'good',work)
        baseline_ok=good['exit']==0 and good['collected']>=task['min_tests'] and good['errors']==0 and good['skipped']==0
        bad=run(task,args.variant,work) if baseline_ok else None
    sensitive=bool(bad and bad['exit']==1 and bad['errors']==0 and bad['skipped']==0 and bad['assertion_failures']>0)
    report=dict(task=args.key,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),baseline_ok=baseline_ok,detected=sensitive,good=good,bad=bad)
    folder=ROOT/'reports';folder.mkdir(exist_ok=True);path=folder/('sensitivity-'+uuid.uuid4().hex+'.json');path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(baseline_ok=baseline_ok,detected=sensitive,report=str(path)),ensure_ascii=True))
    if not baseline_ok:print(good['output']);raise SystemExit(1)
    if not sensitive:print((bad or {}).get('output',''));raise SystemExit('The test did not demonstrate an assertion failure on this defect.')
if __name__=='__main__':main()
