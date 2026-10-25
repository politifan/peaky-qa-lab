import sqlite3,json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'qa.sqlite').resolve()
with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as c:
    c.row_factory=sqlite3.Row
    print(json.dumps([dict(r) for r in c.execute('SELECT id,owner,title,operation_key FROM tickets ORDER BY id')],ensure_ascii=False))
