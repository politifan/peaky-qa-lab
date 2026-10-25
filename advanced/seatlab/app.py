import os,time,uuid
from pathlib import Path
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel,Field,StrictInt
from sqlalchemy import create_engine,Integer,String,Index,select
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

class Base(DeclarativeBase):pass
class Booking(Base):
    __tablename__='bookings'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    owner:Mapped[str]=mapped_column(String(100))
    key:Mapped[str]=mapped_column(String(100))
    event:Mapped[str]=mapped_column(String(100))
    quantity:Mapped[int]=mapped_column(Integer)
class Input(BaseModel):
    owner:str=Field(min_length=1,max_length=100)
    key:str=Field(min_length=1,max_length=100)
    event:str=Field(min_length=1,max_length=100)
    quantity:StrictInt

_shared=None
def create_app(path,profile='good'):
    global _shared
    if profile not in {'good','quantity','schema','duplicate','volatile','tenant_leak','ui_false_success','slow','shared'}:
        raise ValueError('unknown profile')
    if profile in {'volatile','shared'}:
        if profile=='shared' and _shared is not None:engine=_shared
        else:
            engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
            if profile=='shared':_shared=engine
    else:
        target=Path(path).resolve();target.parent.mkdir(parents=True,exist_ok=True)
        engine=create_engine('sqlite:///'+target.as_posix(),connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    if profile!='duplicate':
        with engine.begin() as connection:
            connection.exec_driver_sql('CREATE UNIQUE INDEX IF NOT EXISTS uq_owner_key ON bookings(owner, key)')
    app=FastAPI(title='SeatLab',version='2.0')
    app.state.engine=engine;app.state.profile=profile
    app.state.events=[]
    def body(row):
        return {'id':str(row.id) if profile=='schema' else row.id,'owner':row.owner,
                'key':row.key,'event':row.event,'quantity':row.quantity}
    @app.get('/health')
    def health():return {'status':'alive'}
    @app.post('/bookings')
    def create(data:Input):
        if profile=='slow':time.sleep(.6)
        if not ((0 if profile=='quantity' else 1)<=data.quantity<=5):
            raise HTTPException(422,'quantity must be 1..5')
        app.state.events.append({'request':data.key,'stage':'api'})
        with Session(engine) as s:
            if profile!='duplicate':
                old=s.scalar(select(Booking).where(Booking.owner==data.owner,Booking.key==data.key))
                if old:
                    if old.event!=data.event or old.quantity!=data.quantity:raise HTTPException(409,'key content conflict')
                    return __import__('fastapi').responses.JSONResponse(body(old),status_code=200)
            row=Booking(**data.model_dump());s.add(row)
            try:s.commit()
            except IntegrityError:
                s.rollback();old=s.scalar(select(Booking).where(Booking.owner==data.owner,Booking.key==data.key))
                if old and old.event==data.event and old.quantity==data.quantity:
                    return __import__('fastapi').responses.JSONResponse(body(old),status_code=200)
                raise HTTPException(409,'key content conflict')
            s.refresh(row);app.state.events.append({'request':data.key,'stage':'db'})
            return __import__('fastapi').responses.JSONResponse(body(row),status_code=201)
    @app.get('/bookings/{identity}')
    def get(identity:int,owner:str=Query(min_length=1)):
        with Session(engine) as s:
            row=s.get(Booking,identity)
            if row is None or (row.owner!=owner and profile!='tenant_leak'):raise HTTPException(404,'not found')
            return body(row)
    @app.get('/bookings')
    def listing(owner:str=Query(min_length=1)):
        with Session(engine) as s:
            return [body(x) for x in s.scalars(select(Booking).where(Booking.owner==owner).order_by(Booking.id))]
    @app.get('/',response_class=HTMLResponse)
    def home():
        text=(Path(__file__).parent/'index.html').read_text(encoding='utf-8')
        return text.replace('__FALSE_SUCCESS__','true' if profile=='ui_false_success' else 'false')
    return app

if __name__=='__main__':
    import uvicorn
    app=create_app(os.environ.get('SEATLAB_DB','data/seat.db'),os.environ.get('SEATLAB_PROFILE','good'))
    uvicorn.run(app,host='127.0.0.1',port=int(os.environ.get('SEATLAB_PORT','8765')))
