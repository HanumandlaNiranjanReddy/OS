from flask import Flask, render_template, jsonify, send_file
import os
import socket

app = Flask(__name__)

# Configuration
SHARED_DIR = 'shared'
SERVER_PORT = 5001

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_file_info():
    """Get information about shared files"""
    files = []
    
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR)
    
    for filename in os.listdir(SHARED_DIR):
        filepath = os.path.join(SHARED_DIR, filename)
        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            size_mb = file_size / (1024 * 1024)
            
            files.append({
                'name': filename,
                'size': file_size,
                'size_display': f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB",
                'path': filepath
            })
    
    return files

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/files')
def api_files():
    """API endpoint to get file list"""
    files = get_file_info()
    local_ip = get_local_ip()
    
    return jsonify({
        'status': 'success',
        'files': files,
        'peer_info': {
            'ip': local_ip,
            'port': SERVER_PORT
        }
    })

@app.route('/download/<filename>')
def download(filename):
    """Download a file"""
    try:
        filepath = os.path.join(SHARED_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Create shared directory if it doesn't exist
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR)
        print(f"[*] Created shared directory: {SHARED_DIR}")
    
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print("     P2P FILE SHARING - WEB INTERFACE")
    print("="*60)
    print(f"[*] Local IP: {local_ip}")
    print(f"[*] Web Interface: http://127.0.0.1:8000")
    print(f"[*] Network Access: http://{local_ip}:8000")
    print(f"[*] Server Port: {SERVER_PORT}")
    print(f"[*] Shared Directory: {os.path.abspath(SHARED_DIR)}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=False)