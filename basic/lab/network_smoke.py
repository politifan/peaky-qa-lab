"""Проверка уже запущенного uvicorn; никаких текстовых подмен запуска."""
import httpx,uuid,sys,json
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000'
mark=uuid.uuid4().hex
with httpx.Client(base_url=base,timeout=5) as c:
    assert c.get('/health').status_code==200
    payload=dict(owner='smoke-'+mark,key='k',title='run-'+mark)
    a=c.post('/tickets',json=payload);assert a.status_code==201
    b=c.post('/tickets',json=payload);assert b.status_code==200 and a.json()==b.json()
    obj=a.json()
    assert c.get('/tickets/'+str(obj['id']),params={'owner':payload['owner']}).json()==obj
    assert c.get('/tickets/'+str(obj['id']),params={'owner':'foreign-'+mark}).status_code==404
    print(json.dumps(dict(transport='real HTTP',base_url=base,result='passed',attempt=mark),ensure_ascii=False))
