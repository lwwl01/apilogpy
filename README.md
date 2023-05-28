# APILOG
APILOG is a minimal server for collecting logs via API calls over a network. It
is implemented in Python 3 and has very few external dependencies. At present 
data is stored in an SQLite database.

Note that the software is **experimental** at this point.

## The server and the client
The server stores logs from different sources. Clients can POST to a single 
source and the decides what fields and values to send.

When starting the server, the user needs to supply a location for the SQLite
database. This database will then be initialized and a administration token will
be issued. This token can be used to manage sources. When
a source is added, a source specific token will be issued that needs to be
supplied when writing to that source.

At present, data can not be read via the API.

## Setup
### Getting started with apilog.py
The server can be started on a computer with a recent Python 3 installation 
(3.6+). To create a new database and start the server, type (for more options
use the `-h` switch):
```
> ./apilog.py -n my_database.sqlite
New databse created with master token: <your admin token>
Serving on localhost:8080. Ready for connections.
```
The server is now waiting for commands on localhost, port 8080. A client can now
initiate commands. The first action is to add a new source for logging. Using
`curl`, we can send a POST using a bearer token for authentication:
```
>curl --request POST -H "Authorization: Basic <your admin token>"\
  --url http://localhost:8080/api/add_source?pretty\
  -d '{"description":"My source"}'
```
The server responds with:
```
{
  "message": "success",
  "name": "source_e48d6e1e1a2a",
  "source_token": "<your source token>"
}
```
Note that the `source_token` is different from your admin token. The source
token is source specific and applies **only** to API calls to add log entries
for that specific source.

Using the `source_token` we can now add a log entry to the source:
```
> curl --request POST -H "Authorization: Basic <your source token>"\
  --url http://localhost:8080/api/add_entry?pretty\
  -d '{"name":"source_e48d6e1e1a2a",
       "field":"abc",
       "value":"123",
       "timestamp_source":"Jan 1, 1901"}'

{
  "message": "success"
}

```
The entry is now stored in your SQLite database. Note that all data supplied by 
the source will be stored as text.

## API Reference
An overview of the different API routes:

| Route                     | Method | Required token | Data parameters (* = optional)         |
|---------------------------|--------|----------------|----------------------------------------|
|/api/add_entry             |POST    |source          | name, field, value, timestamp_source(*)|
|/api/add_source            |POST    |admin           | description                            |
|/api/change_source_status  |POST    |admin           | name                                   |
|/api/list_sources          |GET     |admin           | -                                      |

Note on `change_source_status`: A source can be active (default) or inactive.
When the source is inactive, no new log entries are accepted by the server.

# Author
lwwl01 - https://github.com/lwwl01 

# License
This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3.