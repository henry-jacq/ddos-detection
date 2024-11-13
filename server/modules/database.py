import psycopg2
import threading

class PostgresSingleton:
    _instance = None
    _lock = threading.Lock()  # Ensures thread safety

    def __new__(cls, config=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize_connection(config)
            return cls._instance

    def _initialize_connection(self, config):
        # Initializes the connection using provided configuration
        postgres_config = config.get("postgres")
        self.host = postgres_config['host']
        self.database = postgres_config['database']
        self.user = postgres_config['user']
        self.password = postgres_config['password']

        try:
            self.connection = psycopg2.connect(
                host=self.host,
                dbname=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            print("[+] PostgreSQL connection established.")
        except Exception as error:
            print(f"[-] Error while connecting to PostgreSQL: {error}")
            raise

    def execute_query(self, query, params=None):
        if not self.cursor:
            raise Exception("[-] Database connection is not established.")
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as error:
            print(f"[-] Error executing query: {error}")
            self.connection.rollback()
            return None

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("[-] PostgreSQL connection closed.")

def init_db(config):
    return PostgresSingleton(config)
