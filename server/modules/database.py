import psycopg2
import threading

class PostgresSingleton:
    _instance = None
    _lock = threading.Lock()  # To handle thread safety

    def __new__(cls, config=None):
        with cls._lock:
            if cls._instance is None:
                # Create a new instance if one doesn't exist yet
                cls._instance = super().__new__(cls)
                cls._instance._initialize_connection(config)
            return cls._instance

    def _initialize_connection(self, config):
        # Initializes the connection to the PostgreSQL database.
        self.connection = None
        self.cursor = None
        postgres_config = config.get("postgres")

        # Use configuration data if provided
        self.host = postgres_config['host']
        self.database = postgres_config['database']
        self.user = postgres_config['user']
        self.password = postgres_config['password']

        try:
            # Establishing a connection to the database
            self.connection = psycopg2.connect(
                host=self.host,
                dbname=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            print("PostgreSQL connection established.")
        except Exception as error:
            print(f"Error while connecting to PostgreSQL: {error}")
            raise

    # Executes a query and returns the result.
    def execute_query(self, query, params=None):
        if not self.cursor:
            raise Exception("Database connection is not established.")

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as error:
            print(f"Error executing query: {error}")
            self.connection.rollback()
            return None

    # Closes the PostgreSQL connection.
    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("PostgreSQL connection closed.")

# Initialize the database with configuration
def init_db(config):
    # Get the Singleton instance with configuration data
    return PostgresSingleton(config)
