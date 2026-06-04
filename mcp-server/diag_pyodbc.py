import pyodbc
import os
import traceback


def main():
    try:
        print('pyodbc drivers:', pyodbc.drivers())
    except Exception as e:
        print('pyodbc.drivers() error:', e)

    cs = os.environ.get('AZURE_SQL_CONN_STR')
    print('AZURE_SQL_CONN_STR set:', bool(cs))

    if not cs:
        print('No connection string; ensure AZURE_SQL_CONN_STR is set in environment or .env')
        return

    try:
        conn = pyodbc.connect(cs, timeout=5)
        conn.close()
        print('Connection test: success')
    except Exception:
        print('Connection test: exception')
        traceback.print_exc()


if __name__ == '__main__':
    main()
