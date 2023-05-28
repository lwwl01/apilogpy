from http.server import BaseHTTPRequestHandler
import json

class APIServer(BaseHTTPRequestHandler):

    def __init__(self, database, *args, **kwargs):
        
        self.database = database

        self.api_routes = {
            '/api/add_entry' : {
                'function'  : self.store_data, 
                'method'    : 'POST',
                'auth'      : True,
                'auth_type' : 'source' 
            },
            '/api/add_source': {
                'function'  : self.new_source, 
                'method'    : 'POST',
                'auth'      : True,
                'auth_type' : 'main' 
            },
            '/api/change_source_status': {
                'function'  : self.change_source_status, 
                'method'    : 'POST',
                'auth'      : True,
                'auth_type' : 'main' 
            },
            '/api/list_sources': {
                'function'  : self.api_list_sources, 
                'method'    : 'GET',
                'auth'      : True,
                'auth_type' : 'main' 
            }
        }

        super().__init__(*args, **kwargs)

    """
    Support functions to handle requests
    """
    def parse_url(self, path):
        try:
            base_path, options = path.split('?')
        except:
            base_path, options = path, None, False
        
        if options == 'pretty':
            pretty = True
        else:
            pretty = False
        return base_path, pretty

    def check_path(self, path, header, data = None, method = 'GET'):
        routes = self.api_routes
        path, pretty = self.parse_url(self.path)
        
        # Path and method
        paths = routes.keys()     
        path_ok = path in paths
        method_ok = False
        auth_ok = False
        if path_ok:
            method_ok = method in routes[path]['method']
        
        if path_ok:
            if routes[path]['auth']:
                supplied_token = header['Authorization']
                if supplied_token is not None:
                    if routes[path]['auth_type'] == 'main':
                        token_for_table = 'main'
                    else:
                        try:
                            token_for_table = data['name']
                        except:
                            return path_ok, method_ok, auth_ok, path, pretty
                    if self.database.check_credential(
                        supplied_token, 
                        token_for_table = token_for_table):
                        auth_ok = True

        return path_ok, method_ok, auth_ok, path, pretty

    
    def send_error_back(self, http_status = 501, pretty = False):
        if http_status == 404:
            http_message = 'not found'
        elif http_status == 405:
            http_message = 'method not allowed'
        elif http_status == 400:
            http_message = 'bad request'
        elif http_status == 401:
            http_message = 'unauthorized'
        else:
            http_message = 'not implemented'
        
        self.send_response(http_status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(
            self.format_json_output({'message': http_message}, pretty = pretty))
        
    
    def reply_to_request(self, data, pretty = False):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        self.wfile.write(
            self.format_json_output(data, pretty = pretty))
        
    
    def format_json_output(self, data_dict, pretty = False):
        if pretty:
            return bytes(json.dumps(data_dict, sort_keys=True , indent=2) + '\n', 'utf-8')
        else:
            return bytes(json.dumps(data_dict, sort_keys=True) + '\n', 'utf-8')
    
    def check_data(self, data):
        try:
            data = json.loads(data.decode('utf-8'))
            data_ok = True

        except:
            data = json.loads('{}')
            data_ok = False
        
        return data, data_ok

    """
    Core HTTP functions
    """
    def do_GET(self):
        (path_ok, 
         method_ok,
         auth_ok, 
         clean_path, 
         pretty) = self.check_path(path = self.path, 
                                   header = self.headers, 
                                   method = 'GET')
        
        if not path_ok:
            self.send_error_back(404, pretty = pretty)

        elif not method_ok:
            self.send_error_back(405, pretty = pretty)
        
        elif not auth_ok:
            self.send_error_back(401, pretty = pretty)

        else:
            # Execute user function
            try:
                return self.api_routes[clean_path]['function'](pretty)
            except:
                return self.send_error_back(400, pretty = pretty)


    def do_POST(self):
        # Extract data from request
        try:
            length = int(self.headers['Content-Length'])
        except:
            length = 0

        in_data = self.rfile.read(length)
        if len(in_data) > 0:
            data, data_ok = self.check_data(in_data)
        else:
            data = None
            data_ok = True

        (path_ok, 
         method_ok,
         auth_ok, 
         clean_path, 
         pretty) = self.check_path(path = self.path, 
                                   header = self.headers, 
                                   data = data, 
                                   method = 'POST')
        
        if not path_ok:
            return self.send_error_back(404, pretty = pretty)

        elif not method_ok:
            return self.send_error_back(405, pretty = pretty)

        elif not auth_ok:
            return self.send_error_back(401, pretty = pretty)
    
        elif not data_ok:
            return self.send_error_back(399, pretty = pretty)
        
        else:
            # Execute user function
            try:
                return self.api_routes[clean_path]['function'](data, pretty)
            except:
                return self.send_error_back(400, pretty = pretty)


    """
    User actions
    """
    def api_list_sources(self, pretty):
        sources = self.database.list_sources()

        # Setup data for response
        data = []
        for source in sources:
            entry = {}
            entry['name'] = source[1]
            entry['description'] = source[2]
            entry['status'] = source[3]
            entry['source_token'] = source[4]
            data.append(entry)
        
        # Write response
        return self.reply_to_request(data, pretty = pretty)

       
    def change_source_status(self, data, pretty):
        # Extract source id
        if 'name' not in data.keys():
            success = False
        else:
            source_id = data['name']
            # Set status
            success = self.database.change_source_status(source_id)
        
        # Write response
        if success:
            return self.reply_to_request({'message': 'success'}, pretty = pretty)
        else:
            return self.send_error_back(400, pretty = pretty)
            

    def new_source(self, data, pretty):
        # Extract description of new source
        if 'description' not in data.keys():
            return self.send_error_back(400, pretty = pretty)
        else:
            new_name = data['description']
            source_name, source_token = self.database.add_source(new_name)
            return self.reply_to_request({
                'message': 'success',
                'name': source_name,
                'source_token' : source_token
                }, pretty = pretty)
    
    def store_data(self, data, pretty):
        # Extract data from request
        if not all(item in data.keys() for item in ['name', 'value', 'field']):
            return self.send_error_back(400, pretty = pretty)
        
        # Check if source exists
        name = data['name']
        source = self.database.list_sources('source_table')
        if name not in source:
            return self.send_error_back(400, pretty = pretty)
        
        # Check that source is active
        status = self.database.list_single_source(name)
        if status[3] != 'active':
            return self.send_error_back(400, pretty = pretty)
        
        # Source is there, store data  
        field = data['field']
        value = data['value']
        if 'timestamp_source' in data.keys():
            timestamp = data['timestamp_source']
            self.database.insert_item(name, field, value, timestamp)
        else:
            self.database.insert_item(name, field, value)
        return self.reply_to_request({'message': 'success'}, pretty = pretty)

            





    