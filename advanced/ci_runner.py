import subprocess,sys,json,hashlib,argparse
from pathlib import Path
def run(test_path,out,commit):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report=out/'junit.xml'
    result=subprocess.run([sys.executable,'-m','pytest',test_path,'--junitxml='+str(report)],capture_output=True,text=True)
    (out/'pytest.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    index={'commit':commit,'exit_code':result.returncode,'junit':report.name,
           'sha256':hashlib.sha256(report.read_bytes()).hexdigest() if report.exists() else None}
    (out/'index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    return result.returncode
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tests',default='tests');p.add_argument('--out',default='artifacts/local');p.add_argument('--commit',required=True);a=p.parse_args()
    raise SystemExit(run(a.tests,a.out,a.commit))
