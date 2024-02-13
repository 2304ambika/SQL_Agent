import sqlite3
from sqlite3 import Error
import json
from datetime import datetime


class SQLiteManager:
    def __init__(self):
        self.conn = None
        self.cur = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def connect_with_url(self, url):
        self.conn = sqlite3.connect(url)
        self.cur = self.conn.cursor()

    def upsert(self, table_name, _dict):
        columns = _dict.keys()
        values = [":{}".format(col) for col in columns]
        upsert_stmt = "INSERT OR REPLACE INTO {} ({}) VALUES ({})".format(
            table_name, ", ".join(columns), ", ".join(values)
        )
        self.cur.execute(upsert_stmt, _dict)
        self.conn.commit()

    def delete(self, table_name, _id):
        delete_stmt = "DELETE FROM {} WHERE id = :id".format(table_name)
        self.cur.execute(delete_stmt, {"id": _id})
        self.conn.commit()

    def get(self, table_name, _id):
        select_stmt = "SELECT * FROM {} WHERE id = :id".format(table_name)
        self.cur.execute(select_stmt, {"id": _id})
        return self.cur.fetchone()

    def get_all(self, table_name):
        select_all_stmt = "SELECT * FROM {}".format(table_name)
        self.cur.execute(select_all_stmt)
        return self.cur.fetchall()

    def run_sql(self, sql) -> str:
        self.cur.execute(sql)
        columns = [desc[0] for desc in self.cur.description]
        res = self.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        return json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)

    def datetime_handler(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    def get_table_definition(self, table_name):
        get_def_stmt = "PRAGMA table_info({})".format(table_name)
        self.cur.execute(get_def_stmt)
        rows = self.cur.fetchall()
        create_table_stmt = "CREATE TABLE {} (\n".format(table_name)
        for row in rows:
            create_table_stmt += "{} {},\n".format(row[1], row[2])
        create_table_stmt = create_table_stmt.rstrip(",\n") + "\n);"
        return create_table_stmt

    def get_all_table_names(self):
        get_all_tables_stmt = "SELECT name FROM sqlite_master WHERE type='table';"
        self.cur.execute(get_all_tables_stmt)
        return [row[0] for row in self.cur.fetchall()]

    def get_table_definitions_for_prompt(self):
        table_names = self.get_all_table_names()
        definitions = []
        for table_name in table_names:
            definitions.append(self.get_table_definition(table_name))
        return "\n\n".join(definitions)
    

if __name__=="__main__":
    DB_URL = "sqlite-agent-with-autogen\chinook.db"
    
    with SQLiteManager() as db:
        db.connect_with_url(DB_URL)
        print(db.cur.execute("select count(*) from customers"))
        print(db.cur.fetchall())