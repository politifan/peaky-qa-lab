"""Рабочая среда примеров. Содержательные проверки пишет ученик."""
import os,threading,socket,time
from pathlib import Path
import pytest,uvicorn
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from seatlab.app import create_app
def pytest_addoption(parser):
    parser.addoption('--browser',choices=['chromium','firefox'],default='chromium')
    parser.addoption('--profile',default='good')
@pytest.fixture
def client(tmp_path,request):
    with TestClient(create_app(str(tmp_path/'api.db'),request.config.getoption('--profile'))) as c:
        yield c
        c.app.state.engine.dispose()
@pytest.fixture
def live_url(tmp_path,request):
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    app=create_app(str(tmp_path/'ui.db'),request.config.getoption('--profile'))
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.05)
    if not server.started:server.should_exit=True;raise RuntimeError('live server failed to start')
    try:yield 'http://127.0.0.1:'+str(port)
    finally:server.should_exit=True;thread.join(timeout=10);app.state.engine.dispose()
@pytest.fixture
def page(request,tmp_path):
    with sync_playwright() as p:
        browser=getattr(p,request.config.getoption('--browser')).launch(headless=True)
        context=browser.new_context();context.tracing.start(screenshots=True,snapshots=True,sources=True)
        value=context.new_page()
        try:yield value
        finally:
            value.screenshot(path=str(tmp_path/'last-page.png'),full_page=True)
            context.tracing.stop(path=str(tmp_path/'trace.zip'));context.close();browser.close()
