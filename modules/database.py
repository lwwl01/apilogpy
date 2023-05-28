import sqlite3 as sql
from datetime import datetime as dt, timezone
import uuid
import secrets

class SQLiteDatabase:
    """SQLite Database management class."""
    def __init__(self, path = None):
        if path is not None:
            self.connection = sql.connect(path)
        else:
            self.connection = sql.connect(':memory:')
        self.cur = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    # Authentication
    def retrieve_token(self, token_for_table = 'main'):
        if token_for_table == 'main':
            self.cur.execute('''
                SELECT value FROM configuration WHERE field = (?);
                ''', ('api_token',))
        else:
            self.cur.execute('''
                SELECT token FROM sources WHERE source_table = (?);
                ''', (token_for_table,))
        
        token = self.cur.fetchone()[0]
        
        return token
            

    # Configuration section
    def check_configuration(self):
        self.cur.execute('''
            SELECT name FROM sqlite_master WHERE type='table';
            ''')
        tables = []
        for table in self.cur.fetchall():
            tables.append(table[0])

        if ('configuration' in tables) & ('sources' in tables):
            configuration_exists = True
        else:
            configuration_exists = False
        
        return configuration_exists
        
    def create_configuration(self):
        # Check for a current configuration
        if self.check_configuration():
            print('Configuration already exists, skipping initialization')
            return None
        
        else:
            # Create new configuration
            self.cur.execute('''CREATE TABLE IF NOT EXISTS configuration(
                config_id integer PRIMARY KEY, 
                field text,
                value text
                );''')
            self.connection.commit()

            # Store an initial API token
            api_token = secrets.token_urlsafe()
            self.cur.execute('''INSERT INTO configuration(field, value)
                VALUES (?,?)''', ('api_token', api_token))
            
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sources(
                source_id integer PRIMARY KEY,
                source_table text,
                description text,
                status text,
                token text
                );''')
            self.connection.commit()

            return api_token

    def check_credential(self, supplied_token, token_for_table = 'main'):
        token ='Basic '+ self.retrieve_token(token_for_table = token_for_table)
        if secrets.compare_digest(supplied_token, token):
            return True
        else:
            return False

    def renew_token(self, existing_token):
        valid_token = self.check_credential(existing_token)
        if valid_token:
            api_token = secrets.token_urlsafe()
            self.cur.execute('''
                UPDATE configuration SET value = (?) WHERE field = 'api_token';
                ''', (api_token,))
            self.connection.commit()
            return api_token
        else:
            return None

    

    # Sources section
    def add_source(self, name = None):
        self.cur.execute('''SELECT source_table FROM sources;''')
        existing_names = []
        for ids in self.cur.fetchall():
            existing_names.append(ids)

        # Make sure we get uuid that is not already used
        while True:
            source_name = str(uuid.uuid4()).split('-')[4]
            table_name = 'source_' + source_name
            clean_name = self.clean_table_name(table_name)
            if clean_name not in existing_names:
                break
        source_token = secrets.token_urlsafe()
        
        self.cur.execute('''INSERT INTO 
            sources(description, source_table, status, token) VALUES (?, ?, ?, ?);
            ''', (name, clean_name, 'active', source_token))
        self.cur.execute(f'''CREATE TABLE IF NOT EXISTS {clean_name}(
            log_id integer PRIMARY KEY,
            timestamp_server_unix_ms UNSIGNED BIG INT,
            timestamp_source text,
            field text,
            value text
            );''')
        self.connection.commit()

        return clean_name, source_token

    def list_sources(self, names_only = False):
        self.cur.execute('''SELECT * FROM sources;''')
        sources = self.cur.fetchall()
        
        if names_only:
            names = []
            for source in sources:
                names.append(source[1])

            return names
        
        return sources

    def list_single_source(self, source_name):
        self.cur.execute('''SELECT * FROM sources WHERE source_table = (?);''',
                         (source_name,))
        source = self.cur.fetchone()
        
        return source

    def change_source_status(self, source_table = None):
        if source_table is not None:
            self.cur.execute('''SELECT status FROM sources 
                WHERE source_table = (?);''', (source_table,))
            status = self.cur.fetchone()
            print(status)
            if status is None:
                print(f'Id {source_table} does not exist')
                return False
            
            else:
                if status[0] == 'active':
                    new_status = 'inactive'
                else:
                    new_status = 'active'
                
                self.cur.execute('''UPDATE sources SET status = (?) 
                    WHERE source_table = (?);''', (new_status, source_table))
                self.connection.commit()

                return True
        
        else:
            return False
    
    # Logs section
    def insert_item(self, source_table, field, value, timestamp_source = None):
        clean_name = self.clean_table_name(source_table)
        timestamp = int(dt.now(timezone.utc).timestamp()*1000000)
        try:
            self.cur.execute(f'''INSERT INTO 
                {clean_name}(timestamp_server_unix_ms, field, value, timestamp_source) 
                VALUES (?, ?, ?, ?);''', 
                (timestamp, str(field), str(value), str(timestamp_source)))
            self.connection.commit()
        except:
            raise Exception('Source does not exist')
        
    # Other functions
    def clean_table_name(self, name):
        '''Clean table name to prevent injection'''
        clean_name = ''.join(c for c in name if (c.isalnum() | (c == '_')))
        return clean_name
        