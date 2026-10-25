"""Публичная функциональная проба. Скрытая аттестация остаётся у автора."""
import argparse,json,uuid
from fastapi.testclient import TestClient
from seatlab.app import create_app
def probe(path,profile):
    mark=uuid.uuid4().hex;data={'owner':'probe-'+mark,'key':mark,'event':'demo','quantity':2}
    with TestClient(create_app(path,profile)) as c:
        first=c.post('/bookings',json=data);assert first.status_code==201
        row=first.json();assert type(row['id']) is int
        repeat=c.post('/bookings',json=data);assert repeat.status_code==200
        assert repeat.json()['id']==row['id']
    with TestClient(create_app(path,profile)) as c:
        saved=c.get('/bookings/'+str(row['id']),params={'owner':data['owner']})
        assert saved.status_code==200 and saved.json()['quantity']==2
    return {'mark':mark,'profile':profile,'passed':True}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/probe.db');p.add_argument('--profile',default='good');a=p.parse_args()
    print(json.dumps(probe(a.db,a.profile)))
