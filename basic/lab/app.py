"""Учебные данные. Owner — метка, не промышленная аутентификация."""
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, Response
from sqlalchemy import create_engine, select, UniqueConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.pool import StaticPool

class Base(DeclarativeBase):
    pass

class Ticket(Base):
    __tablename__ = 'tickets'
    __table_args__ = (UniqueConstraint('owner', 'operation_key'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(100))
    operation_key: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(120))

def validate_title(value, fault):
    if fault == 'validation':
        return str(value).strip()[:121]
    if not isinstance(value, str):
        raise HTTPException(422, 'title must be string')
    title = value.strip()
    if not 1 <= len(title) <= 120:
        raise HTTPException(422, 'title length 1..120')
    return title

def create_app(db_path, fault=None):
    if fault is None:
        config = Path(__file__).with_name('fault.json')
        fault = json.loads(config.read_text(encoding='utf-8'))['mode'] if config.exists() else 'none'
    db_path = Path(db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if fault == 'storage':
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    else:
        engine = create_engine('sqlite:///' + db_path.as_posix(), connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    app = FastAPI(title='Peaky Minds Ticket Lab')
    app.state.engine = engine
    app.state.db_path = str(db_path)
    app.state.fault = fault

    def as_dict(t):
        return {'id': t.id, 'owner': t.owner, 'title': t.title}

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.post('/tickets')
    def create(payload: dict, response: Response):
        title = validate_title(payload.get('title'), fault)
        owner, key = payload.get('owner'), payload.get('key')
        if not isinstance(owner, str) or not owner.strip() or len(owner) > 100:
            raise HTTPException(422, 'owner required')
        if not isinstance(key, str) or not key.strip() or len(key) > 100:
            raise HTTPException(422, 'key required')
        if fault == 'constant':
            response.status_code = 201
            return {'id': 1, 'owner': 'u', 'title': 'x'}
        with Session(engine) as session:
            old = session.scalar(select(Ticket).where(Ticket.owner == owner, Ticket.operation_key == key))
            if old is not None and fault != 'retry':
                if old.title != title:
                    raise HTTPException(409, 'key already used with different title')
                response.status_code = 200
                return as_dict(old)
            if fault == 'retry':
                count = len(session.scalars(select(Ticket)).all())
                key = key + '-duplicate-' + str(count)
            t = Ticket(owner=owner, operation_key=key, title=title)
            session.add(t)
            session.commit()
            session.refresh(t)
            response.status_code = 201
            return as_dict(t)

    @app.get('/tickets/{ticket_id}')
    def read(ticket_id: int, owner: str):
        if fault == 'constant':
            return {'id': 1, 'owner': 'u', 'title': 'x'}
        if fault == 'always404':
            raise HTTPException(404, 'not found')
        with Session(engine) as session:
            query = select(Ticket).where(Ticket.id == ticket_id)
            if fault != 'isolation':
                query = query.where(Ticket.owner == owner)
            t = session.scalar(query)
            if t is None:
                raise HTTPException(404, 'not found')
            return as_dict(t)

    @app.get('/tickets')
    def listing(owner: str):
        if fault == 'constant':
            return [{'id': 1, 'owner': 'u', 'title': 'x'}]
        if fault == 'always404':
            return []
        with Session(engine) as session:
            query = select(Ticket).order_by(Ticket.id)
            if fault != 'isolation':
                query = query.where(Ticket.owner == owner)
            return [as_dict(t) for t in session.scalars(query)]
    return app

app = create_app(Path(__file__).resolve().parents[1] / 'qa.sqlite')
