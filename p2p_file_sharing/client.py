import socket
import json
import os
import hashlib
from datetime import datetime

class PeerClient:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        
        # Create download directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.download_dir = f"{download_dir}_{timestamp}"
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"[*] Created download directory: {self.download_dir}")
    
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
    
    def connect_to_peer(self, peer_ip, peer_port):
        """Create connection to peer"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, peer_port))
            return client_socket
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return None
    
    def list_files(self, peer_ip, peer_port):
        """List files available on peer"""
        client_socket = self.connect_to_peer(peer_ip, peer_port)
        if not client_socket:
            return None
        
        try:
            # Send LIST command
            request = json.dumps({'command': 'LIST'})
            client_socket.send(request.encode('utf-8'))
            
            # Receive file list
            response = client_socket.recv(4096).decode('utf-8')
            response_data = json.loads(response)
            
            if response_data.get('status') == 'success':
                return response_data.get('files', [])
            else:
                print(f"[-] Error: {response_data.get('message')}")
                return None
        
        except Exception as e:
            print(f"[-] Error listing files: {e}")
            return None
        
        finally:
            client_socket.close()
    
    def download_file(self, peer_ip, peer_port, filename):
        """Download file from peer"""
        client_socket = self.connect_to_peer(peer_ip, peer_port)
        if not client_socket:
            return False
        
        try:
            # Send DOWNLOAD command
            request = json.dumps({
                'command': 'DOWNLOAD',
                'filename': filename
            })
            client_socket.send(request.encode('utf-8'))
            
            # Receive file metadata
            metadata = client_socket.recv(4096).decode('utf-8')
            metadata_data = json.loads(metadata)
            
            if metadata_data.get('status') != 'success':
                print(f"[-] Error: {metadata_data.get('message')}")
                return False
            
            file_size = metadata_data.get('size')
            expected_checksum = metadata_data.get('checksum')
            
            print(f"[*] Downloading: {filename} ({file_size} bytes)")
            
            # Send ready signal
            client_socket.send('READY'.encode('utf-8'))
            
            # Receive file data
            filepath = os.path.join(self.download_dir, filename)
            bytes_received = 0
            
            with open(filepath, 'wb') as f:
                while bytes_received < file_size:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
                    
                    # Show progress
                    progress = (bytes_received / file_size) * 100
                    print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            
            # Verify checksum
            actual_checksum = self.calculate_checksum(filepath)
            
            if actual_checksum == expected_checksum:
                print(f"[+] Download complete: {filename}")
                print(f"[+] Checksum verified: ✓")
                print(f"[+] Saved to: {filepath}")
                return True
            else:
                print(f"[-] Checksum mismatch!")
                print(f"    Expected: {expected_checksum}")
                print(f"    Got: {actual_checksum}")
                return False
        
        except Exception as e:
            print(f"[-] Error downloading file: {e}")
            return False
        
        finally:
            client_socket.close()
    
    def interactive_mode(self):
        """Run client in interactive mode"""
        print("\n" + "="*50)
        print("     P2P FILE SHARING - CLIENT")
        print("="*50)
        
        try:
            peer_ip = input("\nEnter peer IP address: ").strip()
            peer_port = int(input("Enter peer port (default 5001): ").strip() or "5001")
            
            while True:
                print("\n" + "-"*50)
                print("1. List available files")
                print("2. Download file")
                print("3. Exit")
                print("-"*50)
                
                choice = input("Enter your choice: ").strip()
                
                if choice == '1':
                    print("\n[*] Fetching file list...")
                    files = self.list_files(peer_ip, peer_port)
                    
                    if files:
                        print("\n" + "="*50)
                        print("AVAILABLE FILES:")
                        print("="*50)
                        for idx, file_info in enumerate(files, 1):
                            size_mb = file_info['size'] / (1024 * 1024)
                            print(f"{idx}. {file_info['name']}")
                            print(f"   Size: {size_mb:.2f} MB ({file_info['size']} bytes)")
                        print("="*50)
                    else:
                        print("[-] No files available or connection failed")
                
                elif choice == '2':
                    filename = input("\nEnter filename to download: ").strip()
                    if filename:
                        self.download_file(peer_ip, peer_port, filename)
                    else:
                        print("[-] Invalid filename")
                
                elif choice == '3':
                    print("\n[*] Exiting...")
                    break
                
                else:
                    print("[-] Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\n[*] Interrupted by user")
        except Exception as e:
            print(f"\n[-] Error: {e}")

if __name__ == '__main__':
    client = PeerClient()
    client.interactive_mode()