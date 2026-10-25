"""Эталон портфолио 3. Не включать в student ZIP."""
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,StrictInt,model_validator
from sqlalchemy import create_engine,String,Integer,select
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,Session
class Base(DeclarativeBase):pass
class Run(Base):
    __tablename__='runs'
    created_order:Mapped[int]=mapped_column(Integer,primary_key=True)
    attempt:Mapped[str]=mapped_column(String,unique=True)
    commit:Mapped[str]=mapped_column(String)
    tests:Mapped[int]=mapped_column(Integer)
    failures:Mapped[int]=mapped_column(Integer)
    errors:Mapped[int]=mapped_column(Integer)
    skipped:Mapped[int]=mapped_column(Integer)
    exit_code:Mapped[int]=mapped_column(Integer)
    artifact_hash:Mapped[str]=mapped_column(String)
class Input(BaseModel):
    attempt:str=Field(min_length=1,max_length=100)
    commit:str=Field(min_length=1,max_length=100)
    tests:StrictInt=Field(ge=0)
    failures:StrictInt=Field(ge=0)
    errors:StrictInt=Field(ge=0)
    skipped:StrictInt=Field(ge=0)
    exit_code:StrictInt=Field(ge=0)
    artifact_hash:str=Field(min_length=1)
    @model_validator(mode='after')
    def consistent(self):
        if self.failures+self.errors+self.skipped>self.tests:raise ValueError('inconsistent counts')
        return self
def create_app(path):
    engine=create_engine('sqlite:///'+str(path).replace('\\','/'),connect_args={'check_same_thread':False});Base.metadata.create_all(engine)
    app=FastAPI();app.state.engine=engine
    def body(row):return {name:getattr(row,name) for name in ('attempt','commit','tests','failures','errors','skipped','exit_code','artifact_hash','created_order')}
    @app.post('/runs')
    def post(data:Input):
        from fastapi.responses import JSONResponse
        from sqlalchemy.exc import IntegrityError
        with Session(engine) as s:
            old=s.scalar(select(Run).where(Run.attempt==data.attempt))
            if old:
                if {k:getattr(old,k) for k in data.model_dump()}!=data.model_dump():raise HTTPException(409,'attempt conflict')
                return JSONResponse(body(old),status_code=200)
            row=Run(**data.model_dump());s.add(row)
            try:s.commit()
            except IntegrityError:
                s.rollback();old=s.scalar(select(Run).where(Run.attempt==data.attempt))
                if old and {k:getattr(old,k) for k in data.model_dump()}==data.model_dump():return JSONResponse(body(old),status_code=200)
                raise HTTPException(409,'attempt conflict')
            s.refresh(row);return JSONResponse(body(row),status_code=201)
    @app.get('/runs')
    def listing():
        with Session(engine) as s:return [body(r) for r in s.scalars(select(Run).order_by(Run.created_order))]
    @app.get('/runs/{attempt}')
    def get(attempt:str):
        with Session(engine) as s:
            row=s.scalar(select(Run).where(Run.attempt==attempt))
            if row is None:raise HTTPException(404,'missing')
            return body(row)
    @app.get('/gate/{attempt}')
    def gate(attempt:str,expected_commit:str,critical_quarantine:int=0):
        row=get(attempt);reasons=[]
        if row['commit']!=expected_commit:reasons.append('provenance')
        if row['tests']==0:reasons.append('empty')
        if row['failures']:reasons.append('failures')
        if row['errors']:reasons.append('errors')
        if row['exit_code']:reasons.append('exit')
        if critical_quarantine>0:reasons.append('quarantine')
        return {'release':not reasons,'reasons':sorted(reasons)}
    @app.get('/summary')
    def summary():
        rows=listing();return {'runs':len(rows),**{name:sum(r[name] for r in rows) for name in ('tests','failures','errors','skipped')}}
    return app
