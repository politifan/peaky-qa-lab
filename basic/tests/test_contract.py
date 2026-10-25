import pytest
from fastapi.testclient import TestClient
from lab.app import create_app

@pytest.fixture
def application(tmp_path):
    app=create_app(tmp_path/'test.sqlite')
    yield app
    app.state.engine.dispose()

def payload(owner='u1',key='k1',title='first'):
    return dict(owner=owner,key=key,title=title)

@pytest.mark.parametrize('title',['', ' '*4, 'x'*121, 17, True, None])
def test_validation(application,title):
    with TestClient(application) as c:
        assert c.post('/tickets',json=payload(title=title)).status_code==422
        assert c.get('/tickets',params={'owner':'u1'}).json()==[]

@pytest.mark.parametrize('title',['x','x'*120,'  привет  '])
def test_valid_edges(application,title):
    with TestClient(application) as c:
        r=c.post('/tickets',json=payload(title=title))
        assert r.status_code==201
        obj=r.json()
        assert type(obj['id']) is int and obj['id']>0
        assert obj['title']==title.strip()
        assert c.get('/tickets/'+str(obj['id']),params={'owner':'u1'}).json()==obj

def test_retry(application):
    with TestClient(application) as c:
        a=c.post('/tickets',json=payload())
        b=c.post('/tickets',json=payload())
        assert a.status_code==201 and b.status_code==200
        assert a.json()==b.json()
        conflict=c.post('/tickets',json=payload(title='other'))
        assert conflict.status_code==409
        assert c.get('/tickets',params={'owner':'u1'}).json()==[a.json()]

def test_owner(application):
    with TestClient(application) as c:
        a=c.post('/tickets',json=payload()).json()
        b=c.post('/tickets',json=payload(owner='u2',title='second')).json()
        assert a['id']!=b['id']
        assert c.get('/tickets/'+str(a['id']),params={'owner':'u1'}).status_code==200
        assert c.get('/tickets/'+str(a['id']),params={'owner':'u2'}).status_code==404
        assert c.get('/tickets',params={'owner':'u1'}).json()==[a]
        assert c.get('/tickets',params={'owner':'u2'}).json()==[b]

def test_restart(tmp_path):
    path=tmp_path/'restart.sqlite'
    a=create_app(path)
    with TestClient(a) as c:
        old=c.post('/tickets',json=payload()).json()
    a.state.engine.dispose()
    b=create_app(path)
    try:
        with TestClient(b) as c:
            assert c.get('/tickets/'+str(old['id']),params={'owner':'u1'}).json()==old
            assert c.post('/tickets',json=payload()).json()==old
    finally:
        b.state.engine.dispose()
