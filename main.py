import mimetypes
import os
import socket
from email.utils import formatdate


class TCPServer:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port

    def start(self):
        # socket object creation
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set some options for the socket to reuse local addresses
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at ", s.getsockname())

        while True:
            conn, addr = s.accept()
            print("Connected by ", addr)
            
            # Read complete request with headers and body
            data = b""
            max_size = 1024 * 1024  # 1MB limit
            
            # Read until we have headers
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
                if len(data) > max_size:
                    conn.close()
                    continue
            
            # Check if there's a body to read
            if b"\r\n\r\n" in data:
                header_end = data.index(b"\r\n\r\n") + 4
                headers_part = data[:header_end].decode('iso-8859-1', errors='ignore')
                
                # Extract Content-Length if present
                content_length = 0
                for line in headers_part.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        try:
                            content_length = int(line.split(':', 1)[1].strip())
                        except ValueError:
                            pass
                        break
                
                # Read remaining body
                body_received = len(data) - header_end
                while body_received < content_length:
                    chunk = conn.recv(min(1024, content_length - body_received))
                    if not chunk:
                        break
                    data += chunk
                    body_received += len(chunk)
                    if len(data) > max_size:
                        break

            response = self.handle_request(data)

            conn.sendall(response)
            conn.close()

    def handle_request(self, data):
        # TODO
        return data


class HTTPServer(TCPServer):
    headers = {
        "Server": "My Server",
        "Content-Type": "text/html",
    }

    status_codes = {
        200: "OK",
        201: "Created",
        204: "No Content",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
        501: "Not Implemented"
    }

    def handle_request(self, data):
        request = HTTPRequest(data)
        
        # Check if request is malformed
        if request.malformed:
            return self.HTTP_400_handler()

        # Allowlist of supported methods
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
        
        try:
            if request.method in allowed_methods:
                handler = getattr(self, "handle_%s" % request.method)
                response = handler(request)
            else:
                response = self.HTTP_405_handler()
        except Exception as e:
            print(f"Error handling request: {e}")
            response = self.HTTP_500_handler()

        return response

    def response_line(self, status_code):
        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s \r\n" % (status_code, reason)

        return line.encode()  # converts str to bytes

    def response_headers(self, extra_headers=None, content_length=0):
        headers_copy = self.headers.copy()  # local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)
        
        # Add required headers
        headers_copy['Date'] = formatdate(timeval=None, localtime=False, usegmt=True)
        headers_copy['Content-Length'] = str(content_length)
        headers_copy['Connection'] = 'close'

        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])

        return headers.encode()

    def handle_GET(self, request):
        filename = request.uri.strip("/")
        
        # Normalize path to prevent directory traversal
        filename = os.path.normpath(filename)
        if filename.startswith('..'):
            response_line = self.response_line(status_code=403)
            response_body = b"<h1>403 Forbidden</h1>"
            response_headers = self.response_headers(content_length=len(response_body))
        elif os.path.exists(filename):
            response_line = self.response_line(status_code=200)

            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            extra_headers = {"Content-Type": content_type}

            with open(filename, "rb") as f:
                response_body = f.read()
            
            response_headers = self.response_headers(extra_headers, content_length=len(response_body))
        else:
            response_line = self.response_line(status_code=404)
            response_body = b"<h1>404 Not Found</h1>"
            response_headers = self.response_headers(content_length=len(response_body))

        blank_line = b"\r\n"

        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def handle_POST(self, request):
        # Check for Content-Length header
        if 'content-length' not in request.headers:
            return self.HTTP_400_handler()
        
        # For learning purposes, echo back the received data
        response_line = self.response_line(status_code=200)
        
        # Create response body with info about what was received
        response_body = b"<h1>POST Request Received</h1>"
        response_body += b"<p>URI: " + request.uri.encode() + b"</p>"
        response_body += b"<p>Content-Length: " + str(len(request.body)).encode() + b"</p>"
        response_body += b"<p>Body:</p><pre>" + request.body + b"</pre>"
        
        extra_headers = {"Content-Type": "text/html"}
        response_headers = self.response_headers(extra_headers, content_length=len(response_body))
        
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def handle_PUT(self, request):
        # Check for Content-Length header
        if 'content-length' not in request.headers:
            return self.HTTP_400_handler()
        
        response_line = self.response_line(status_code=200)
        response_body = b"<h1>PUT Request Received</h1>"
        response_body += b"<p>URI: " + request.uri.encode() + b"</p>"
        response_body += b"<p>Content-Length: " + str(len(request.body)).encode() + b"</p>"
        
        extra_headers = {"Content-Type": "text/html"}
        response_headers = self.response_headers(extra_headers, content_length=len(response_body))
        
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def handle_DELETE(self, request):
        response_line = self.response_line(status_code=200)
        response_body = b"<h1>DELETE Request Received</h1>"
        response_body += b"<p>URI: " + request.uri.encode() + b"</p>"
        
        extra_headers = {"Content-Type": "text/html"}
        response_headers = self.response_headers(extra_headers, content_length=len(response_body))
        
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])

    def HTTP_400_handler(self):
        response_line = self.response_line(status_code=400)
        response_body = b"<h1>400 Bad Request</h1>"
        response_headers = self.response_headers(content_length=len(response_body))
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def HTTP_405_handler(self):
        response_line = self.response_line(status_code=405)
        response_body = b"<h1>405 Method Not Allowed</h1>"
        extra_headers = {"Allow": "GET, POST, PUT, DELETE"}
        response_headers = self.response_headers(extra_headers, content_length=len(response_body))
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def HTTP_500_handler(self):
        response_line = self.response_line(status_code=500)
        response_body = b"<h1>500 Internal Server Error</h1>"
        response_headers = self.response_headers(content_length=len(response_body))
        blank_line = b"\r\n"
        return b"".join([response_line, response_headers, blank_line, response_body])


class HTTPRequest:
    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = "1.1"
        self.headers = {}
        self.body = b""
        self.malformed = False

        self.parse(data)

    def parse(self, data):
        try:
            # Split headers and body
            if b"\r\n\r\n" in data:
                headers_part, self.body = data.split(b"\r\n\r\n", 1)
            else:
                headers_part = data
                self.body = b""
            
            lines = headers_part.split(b"\r\n")
            
            if not lines:
                self.malformed = True
                return

            request_line = lines[0]
            words = request_line.split(b" ")
            
            # Validate request line has 3 parts
            if len(words) != 3:
                self.malformed = True
                return

            self.method = words[0].decode()  # convert bytes to str
            self.uri = words[1].decode()
            self.http_version = words[2].decode()
            
            # Parse headers
            for line in lines[1:]:
                if b":" in line:
                    key, value = line.split(b":", 1)
                    self.headers[key.decode().lower()] = value.decode().strip()
        except Exception:
            self.malformed = True


if __name__ == "__main__":
    server = HTTPServer()
    server.start()
