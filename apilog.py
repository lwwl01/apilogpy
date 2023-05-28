#!/usr/bin/env python3

from modules.server import APIServer
from modules.database import SQLiteDatabase
from http.server import HTTPServer
from functools import partial
from os.path import exists
import sys
import argparse

def start_webserver(db, hostname, port):
    # We attach the database to the APIServer args so that we can pass it to
    # the HTTPServer object.
    APIServerWithDB = partial(APIServer, db)
    
    try:
        WebServer = HTTPServer((hostname, port), APIServerWithDB)
    except:
        print('Cannot open server on specified hostname/ip or port.')
        sys.exit()

    try:
        print(f'Serving on {hostname}:{port}. Ready for connections.')
        WebServer.serve_forever()
    except KeyboardInterrupt:
        WebServer.server_close()
        del db
        print("Process terminated by user input.")

if __name__ == "__main__":
    # Handle input arguments
    parser = argparse.ArgumentParser(
                    prog='apilog.py',
                    description='Simple server for logs over networks')
    parser.add_argument('-n', '--new', 
                        help='Setup a new database file', 
                        action='store_true')
    parser.add_argument('--host', 
                        help='Host/ip to serve on (default: localhost).', 
                        default='localhost')
    parser.add_argument('--port', help='Port to serve on. (default: 8080)', 
                        default=8080, type=int)
    parser.add_argument('filename', 
                        help='Path to SQLite database file', 
                        default=None)
    
    arguments = parser.parse_args()
    
    if (not arguments.new) & (exists(arguments.filename)):
        try:
            db = SQLiteDatabase(path = arguments.filename)
            db.check_configuration()
            print('Database loaded')
        except:
            print("Cannot open log database. Incompatible or damaged file.")
            sys.exit()

    elif (arguments.new) & (exists(arguments.filename)):
        print('File already exists.')
        sys.exit()

    elif (arguments.new) & (not exists(arguments.filename)):
        # Create new database
        db = SQLiteDatabase(path = arguments.filename)
        token = db.create_configuration()
        print(f'New databse created with admin token: {token}')
        

    elif not exists(arguments.filename):
        print('Database does not exist')
        sys.exit()

    # Server parameters
    hostname = arguments.host
    port = arguments.port

    # Launch server
    start_webserver(db, hostname, port)

    