import os,sys,json,importlib.util
from fastapi.testclient import TestClient
spec=importlib.util.spec_from_file_location('worker_candidate',os.environ['CANDIDATE_APP'])
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
data=json.load(sys.stdin)
with TestClient(candidate.create_app(sys.argv[2],os.environ.get('APP_PROFILE','good'))) as c:
    if sys.argv[1]=='create':
        response=c.post('/bookings',json=data);assert response.status_code==201
    else:
        response=c.get('/bookings/'+str(data['id']),params={'owner':data['owner']});assert response.status_code==200
    result=response.json();c.app.state.engine.dispose()
print(json.dumps(result))
