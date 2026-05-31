import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5001  # Port beda dari multicast
BUFFER_SIZE = 4096
SAVE_DIR = 'received_files'

clients = {}  # {nama: conn}
clients_lock = threading.Lock()

def broadcast_file(conn, nama_pengirim, nama_file, ukuran_file):
    """Terima file dari pengirim dan forward ke SEMUA client lain"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    save_path = os.path.join(SAVE_DIR, f"dari_{nama_pengirim}_{nama_file}")

    diterima = 0
    with open(save_path, 'wb') as f:
        while diterima < ukuran_file:
            sisa = ukuran_file - diterima
            chunk = conn.recv(min(BUFFER_SIZE, sisa))
            if not chunk:
                break
            f.write(chunk)
            diterima += len(chunk)

    print(f"[SERVER] File '{nama_file}' dari {nama_pengirim} diterima ({diterima} bytes)")

    # Forward ke semua client kecuali pengirim
    with open(save_path, 'rb') as f:
        data_file = f.read()

    with clients_lock:
        for nama, target_conn in clients.items():
            if nama == nama_pengirim:
                continue
            try:
                header = f"FILE|{nama_pengirim}|{nama_file}|{len(data_file)}\n"
                target_conn.sendall(header.encode())
                target_conn.sendall(data_file)
                print(f"[SERVER] File '{nama_file}' diteruskan ke {nama}")
            except Exception as e:
                print(f"[SERVER] Gagal kirim ke {nama}: {e}")

    conn.sendall(b"OK\n")

def broadcast_teks(conn, nama_pengirim, pesan):
    """Forward pesan teks ke semua client kecuali pengirim"""
    print(f"[SERVER] TEKS dari {nama_pengirim} ke semua: {pesan}")
    with clients_lock:
        for nama, target_conn in clients.items():
            if nama == nama_pengirim:
                continue
            try:
                msg = f"TEKS|{nama_pengirim}|{pesan}\n"
                target_conn.sendall(msg.encode())
                print(f"[SERVER] Pesan diteruskan ke {nama}")
            except Exception as e:
                print(f"[SERVER] Gagal kirim ke {nama}: {e}")

    conn.sendall(b"OK\n")

def handle_client(conn, addr):
    nama = None
    try:
        # Terima nama client
        nama = conn.recv(1024).decode().strip()
        with clients_lock:
            clients[nama] = conn
        print(f"[SERVER] {nama} terhubung dari {addr}")
        print(f"[SERVER] Client aktif: {list(clients.keys())}")
        conn.sendall(b"TERHUBUNG\n")

        while True:
            data = b""
            while not data.endswith(b"\n"):
                byte = conn.recv(1)
                if not byte:
                    raise ConnectionResetError("Client disconnect")
                data += byte

            data = data.decode().strip()
            if not data:
                continue

            parts = data.split('|')
            tipe = parts[0]

            # Format: TEKS|pengirim|pesan
            if tipe == 'TEKS':
                pengirim = parts[1]
                pesan = parts[2]
                broadcast_teks(conn, pengirim, pesan)

            # Format: FILE|pengirim|nama_file|ukuran
            elif tipe == 'FILE':
                pengirim = parts[1]
                nama_file = parts[2]
                ukuran_file = int(parts[3])
                print(f"[SERVER] FILE dari {pengirim}: {nama_file} ({ukuran_file} bytes)")
                conn.sendall(b"SIAP\n")
                broadcast_file(conn, pengirim, nama_file, ukuran_file)

    except Exception as e:
        print(f"[SERVER] Error dari {nama or addr}: {e}")
    finally:
        if nama:
            with clients_lock:
                clients.pop(nama, None)
            print(f"[SERVER] {nama} disconnect. Client aktif: {list(clients.keys())}")
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[SERVER BROADCAST] Berjalan di {HOST}:{PORT}")
    print(f"[SERVER BROADCAST] Menunggu koneksi...\n")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    main()