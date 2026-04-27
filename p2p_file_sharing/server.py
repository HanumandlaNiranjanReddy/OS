import socket
import threading
import os
import hashlib
import json

class PeerServer:
    def __init__(self, host='0.0.0.0', port=5001, shared_dir='shared'):
        self.host = host
        self.port = port
        self.shared_dir = shared_dir
        self.server_socket = None
        
        # Create shared directory if it doesn't exist
        if not os.path.exists(self.shared_dir):
            os.makedirs(self.shared_dir)
            print(f"[*] Created shared directory: {self.shared_dir}")
    
    def calculate_checksum(self, filepath):
        """Calculate MD5 checksum of a file"""
        md5_hash = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"[-] Error calculating checksum: {e}")
            return None
    
    def get_file_list(self):
        """Get list of files in shared directory"""
        try:
            files = []
            for filename in os.listdir(self.shared_dir):
                filepath = os.path.join(self.shared_dir, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    files.append({
                        'name': filename,
                        'size': file_size
                    })
            return files
        except Exception as e:
            print(f"[-] Error getting file list: {e}")
            return []
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        print(f"[+] Connection from {address}")
        
        try:
            # Receive request from client
            request = client_socket.recv(1024).decode('utf-8')
            request_data = json.loads(request)
            
            command = request_data.get('command')
            
            if command == 'LIST':
                # Send file list
                files = self.get_file_list()
                response = json.dumps({'status': 'success', 'files': files})
                client_socket.send(response.encode('utf-8'))
                print(f"[+] Sent file list to {address}")
            
            elif command == 'DOWNLOAD':
                filename = request_data.get('filename')
                filepath = os.path.join(self.shared_dir, filename)
                
                if not os.path.exists(filepath):
                    response = json.dumps({'status': 'error', 'message': 'File not found'})
                    client_socket.send(response.encode('utf-8'))
                    print(f"[-] File not found: {filename}")
                    return
                
                # Get file info
                file_size = os.path.getsize(filepath)
                checksum = self.calculate_checksum(filepath)
                
                # Send file metadata
                metadata = json.dumps({
                    'status': 'success',
                    'filename': filename,
                    'size': file_size,
                    'checksum': checksum
                })
                client_socket.send(metadata.encode('utf-8'))
                
                # Wait for acknowledgment
                ack = client_socket.recv(1024).decode('utf-8')
                if ack != 'READY':
                    print(f"[-] Client not ready")
                    return
                
                # Send file data
                print(f"[+] Sending file: {filename} ({file_size} bytes)")
                with open(filepath, 'rb') as f:
                    bytes_sent = 0
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        client_socket.send(chunk)
                        bytes_sent += len(chunk)
                
                print(f"[+] Sent {filename} successfully ({bytes_sent} bytes)")
                print(f"[+] Checksum: {checksum}")
        
        except Exception as e:
            print(f"[-] Error handling client {address}: {e}")
        
        finally:
            client_socket.close()
            print(f"[-] Connection closed: {address}")
    
    def start(self):
        """Start the peer server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            print(f"[*] Peer server started on {self.host}:{self.port}")
            print(f"[*] Sharing files from: {os.path.abspath(self.shared_dir)}")
            print(f"[*] Waiting for incoming connections...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        
        except KeyboardInterrupt:
            print("\n[*] Server shutting down...")
        except Exception as e:
            print(f"[-] Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

if __name__ == '__main__':
    server = PeerServer()
    server.start()