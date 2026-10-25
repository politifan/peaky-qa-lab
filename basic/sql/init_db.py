from pathlib import Path
import sqlite3
p=Path('qa-data.sqlite')
if p.exists():
    raise SystemExit('qa-data.sqlite already exists: use a separate exercise folder; no automatic overwrite')
with sqlite3.connect(p) as c:
    c.executescript(Path(__file__).with_name('seed.sql').read_text(encoding='utf-8'))
print('qa-data.sqlite created')
