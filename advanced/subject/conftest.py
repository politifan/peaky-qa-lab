"""Public baseline fixtures for executable Python work."""
import os, sys, json, uuid, subprocess, importlib.util, threading, socket, time
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
import pytest, httpx, uvicorn
from fastapi.testclient import TestClient
ROOT = Path(__file__).resolve().parents[1]
VARIANT = os.environ.get('PEAKY_QA_VARIANT','good')
APP_VARIANTS={'good','quantity','schema','duplicate','volatile','tenant_leak','ui_false_success','slow','shared'}

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def make_data():
    return lambda **changes: dict(owner=uuid.uuid4().hex, key=uuid.uuid4().hex, event='demo', quantity=1, **{}) | changes

@pytest.fixture
def make_run():
    return lambda: dict(attempt=uuid.uuid4().hex, commit='current', tests=4, failures=0, errors=0, skipped=0, exit_code=0, artifact_hash='sha256:demo')

@pytest.fixture
def candidate_path(tmp_path):
    source = (ROOT / 'seatlab/app.py').read_text(encoding='utf-8')
    path = tmp_path / 'candidate.py'
    path.write_text(source, encoding='utf-8')
    html = (ROOT / 'seatlab/index.html').read_text(encoding='utf-8')
    html = html.replace('</main>', '<button>Забронировать</button></main>')
    (tmp_path / 'index.html').write_text(html, encoding='utf-8')
    return path

@pytest.fixture
def app_factory(candidate_path):
    module = load(candidate_path, 'subject_app_' + uuid.uuid4().hex)
    profile = VARIANT if VARIANT in APP_VARIANTS else 'good'
    apps = []

    def factory(path):
        app = module.create_app(path, profile)
        app.state.profile = profile
        apps.append(app)
        return app
    yield factory
    for app in apps:
        app.state.engine.dispose()

@pytest.fixture
def client(app_factory, tmp_path):
    with TestClient(app_factory(str(tmp_path / 'client.db'))) as c:
        yield c

@pytest.fixture
def dashboard_client(tmp_path):
    source = (ROOT / 'quality_dashboard.py').read_text(encoding='utf-8')
    path = tmp_path / 'dashboard.py'
    path.write_text(source, encoding='utf-8')
    module = load(path, 'subject_dashboard_' + uuid.uuid4().hex)
    app = module.create_app(tmp_path / 'runs.db')
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.state.engine.dispose()

@pytest.fixture
def restart_probe(candidate_path, tmp_path):

    def run(data):
        env = os.environ.copy()
        env['CANDIDATE_APP'] = str(candidate_path)
        env['APP_PROFILE'] = VARIANT if VARIANT in APP_VARIANTS else 'good'

        def action(mode, payload):
            result = subprocess.run([sys.executable, str(ROOT / 'restart_worker.py'), mode, str(tmp_path / 'process.db')], input=json.dumps(payload), text=True, capture_output=True, env=env, timeout=25)
            assert result.returncode == 0, 'restart worker failed: ' + result.stderr[-1800:]
            return json.loads(result.stdout)
        before = action('create', data)
        after = action('read', before)
        return (before, after)
    return run

@pytest.fixture
def target():
    target = SimpleNamespace()
    shared = {'key': 'seed:73', 'tags': []}
    owned = []
    target.payload_factory = lambda seed: shared if VARIANT=='factory_alias' else {'key': 'seed:' + str(seed), 'tags': []}

    @contextmanager
    def resources(log):
        import sqlite3
        db = sqlite3.connect(':memory:')
        log.append('open:db')
        owned.append(db)
        client = httpx.Client()
        log.append('open:client')
        owned.append(client)
        try:
            yield SimpleNamespace(db=db, client=client)
        finally:
            client.close()
            log.append('close:client')
            db.close()
            log.append('close:db')
    target.resources = resources

    class DependencyError(Exception):
        pass
    target.DependencyError = DependencyError

    def availability(client, event):
        try:
            response = client.get('https://provider.test/events/' + event, timeout=1)
        except httpx.TimeoutException as exc:
            raise DependencyError('timeout') from exc
        if response.status_code != 200 and VARIANT != 'dependency_status':
            raise DependencyError('status')
        body = response.json()
        if type(body.get('available')) is not bool and VARIANT != 'dependency_schema':
            raise DependencyError('schema')
        return bool(body.get('available'))
    target.availability = availability
    target.release = lambda row, current: True if VARIANT=='ci_skip' else row['exit_code'] == 0 and row['collected'] > 0 and (row['failed'] == 0) and (row['artifact_commit'] == current) and (row['quarantined_critical'] == 0)
    target.execute = lambda path: subprocess.run([sys.executable, str(path)], timeout=10).returncode

    def counts(path):
        import xml.etree.ElementTree as ET
        suites = list(ET.parse(path).getroot().iter('testsuite'))
        return {key: 0 if key == 'errors' and VARIANT == 'junit_ignores_errors' else sum((int(s.get(key, 0)) for s in suites)) for key in ['tests', 'failures', 'errors', 'skipped']}
    target.junit_counts = counts
    target.now = time.time
    target.expired = lambda expiry: expiry < target.now()
    yield target
    for resource in reversed(owned):
        resource.close()

@pytest.fixture
def live_url(app_factory, tmp_path):
    app = app_factory(str(tmp_path / 'live.db'))
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started, 'server startup timed out'
        yield ('http://127.0.0.1:' + str(port))
    finally:
        server.should_exit = True
        thread.join(10)
        sock.close()

@pytest.fixture
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()
