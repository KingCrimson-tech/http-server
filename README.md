# Simple HTTP Server

A basic HTTP server written in Python from scratch using sockets. This project is meant for learning how HTTP works at a low level.

## What It Does

This server handles basic HTTP requests and serves files from the current directory. It supports the following HTTP methods:

- **GET** - Retrieve files from the server
- **POST** - Send data to the server (echoes back what was received)
- **PUT** - Send data to update a resource (echoes back what was received)
- **DELETE** - Request to delete a resource (acknowledges the request)

## Requirements

- Python 3.x
- No external dependencies (uses only standard library modules)

## How to Run

1. Open a terminal in the project directory
2. Run the server:
   ```
   python main.py
   ```
3. The server will start on `http://127.0.0.1:8888`
4. Open a browser and go to `http://127.0.0.1:8888/index.html` to see it working

## Testing the Server

### Using a Browser

Simply visit `http://127.0.0.1:8888/` followed by any filename in the directory. For example:
- `http://127.0.0.1:8888/index.html`
- `http://127.0.0.1:8888/hello.html`

### Using curl

```
# GET request
curl http://127.0.0.1:8888/index.html

# POST request with data
curl -X POST -d "name=test" http://127.0.0.1:8888/submit

# PUT request
curl -X PUT -d "data=example" http://127.0.0.1:8888/resource

# DELETE request
curl -X DELETE http://127.0.0.1:8888/resource
```

## How It Works

The server is built in three main parts:

1. **TCPServer** - Handles the low-level socket connection. It listens for incoming connections, reads the raw data, and sends responses back.

2. **HTTPServer** - Extends TCPServer to understand HTTP. It parses requests, routes them to the right handler based on the method (GET, POST, etc.), and builds proper HTTP responses with headers.

3. **HTTPRequest** - A helper class that parses raw HTTP request data into usable parts: the method, URI, headers, and body.

## Project Structure

```
http-server/
    main.py      - The server code
    index.html   - A sample HTML file to serve
    hello.html   - Another sample HTML file
    README.md    - This file
```

## TODOs

- Handles one connection at a time (no concurrency)
- Basic error handling
- No HTTPS support
- Limited to a 1MB request size
