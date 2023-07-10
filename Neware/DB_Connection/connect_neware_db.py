from newaresql import newaresql

"""
Connection string format:
- dialect+driver://username:password@host:port/database_name
- sqlite://username:password@your_server_ip:port/database_name
- mysql+pymysql://username:password@your_server_ip:port/database_name
"""

DB_USERNAME = "BtsClient"
DB_PASSWORD = "www.neware.com.cn"
DB_SERVERIP = "192.168.1.250"

DB_USERNAME = "root"
DB_PASSWORD = "^2&^niu7wiwx5^"
DB_SERVERIP = "localhost"
DB_PORT = 3306
DB_NAME = "bts63"


def download_if_active(test):
    """_summary_

    :param test: Test
    :type test: class:`pandas.Sequence`
    """
    return test.active


connection = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVERIP}:{DB_PORT}/{DB_NAME}"
db = newaresql.NewareDB(connection, file_format='csv',
                        file_name=None, file_path=None, download=None)
# parallel=True or int has the risk of Malloc Error
db.download(update=True, parallel=False, n_rows=100)
