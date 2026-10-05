import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'loop.sqlite'
        self.lock = threading.RLock()
        with self.tx() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS records(kind TEXT NOT NULL,id TEXT NOT NULL,owner TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(kind,id));
              CREATE INDEX IF NOT EXISTS records_owner ON records(kind,owner);
              CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,owner TEXT NOT NULL,at REAL NOT NULL,kind TEXT NOT NULL,data TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,owner TEXT NOT NULL,purpose TEXT NOT NULL,mode TEXT NOT NULL,status TEXT NOT NULL,started REAL NOT NULL,finished REAL,request TEXT NOT NULL,result TEXT,error TEXT);
              CREATE INDEX IF NOT EXISTS runs_budget ON runs(owner,mode,purpose,started);
            ''')

    @contextmanager
    def tx(self):
        with self.lock:
            db = sqlite3.connect(self.path, timeout=30)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally: db.close()

    @staticmethod
    def get(db, kind, id):
        row = db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, id)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def rows(db, kind, owner=None):
        sql, args = 'SELECT data FROM records WHERE kind=?', [kind]
        if owner is not None: sql += ' AND owner=?'; args.append(owner)
        return [json.loads(row[0]) for row in db.execute(sql, args)]

    @staticmethod
    def put(db, kind, value):
        db.execute('INSERT INTO records(kind,id,owner,data) VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET owner=excluded.owner,data=excluded.data',
                   (kind, value['id'], value['owner'], json.dumps(value, ensure_ascii=False)))

    @staticmethod
    def event(db, owner, at, kind, data):
        db.execute('INSERT INTO events(owner,at,kind,data) VALUES(?,?,?,?)', (owner, at, kind, json.dumps(data, ensure_ascii=False)))
