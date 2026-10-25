import sqlite3,sys,json
from pathlib import Path
uri=Path('qa-data.sqlite').resolve().as_uri()+'?mode=ro'
with sqlite3.connect(uri,uri=True) as c:
    c.row_factory=sqlite3.Row
    rows=c.execute(Path(sys.argv[1]).read_text(encoding='utf-8')).fetchall()
    print(json.dumps([dict(r) for r in rows],ensure_ascii=False))
