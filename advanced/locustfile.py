from locust import HttpUser,task,between
from uuid import uuid4
class SeatUser(HttpUser):
    wait_time=between(.1,.3)
    def on_start(self):self.owner='load-'+uuid4().hex;self.last=None
    @task(3)
    def create(self):
        data={'owner':self.owner,'key':uuid4().hex,'event':'demo','quantity':1}
        with self.client.post('/bookings',json=data,name='POST bookings',catch_response=True) as r:
            try:
                body=r.json()
                if r.status_code!=201 or type(body.get('id')) is not int or body.get('quantity')!=1:r.failure('contract')
                else:self.last=body['id']
            except ValueError:r.failure('invalid json')
    @task
    def read(self):
        if self.last is None:return
        with self.client.get('/bookings/'+str(self.last),params={'owner':self.owner},name='GET booking',catch_response=True) as r:
            try:
                if r.status_code!=200 or r.json().get('owner')!=self.owner:r.failure('read contract')
            except ValueError:r.failure('invalid json')
