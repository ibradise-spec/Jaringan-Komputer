import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5000
BUFFER_SIZE = 4096
SAVE_DIR = 'received_files'

clients = {}  # {nama: conn}
clients_lock = threading.Lock()

def terima_file(conn, nama_pengirim, nama_file, ukuran_file, tujuan_list):
    """Terima file dari pengirim dan forward ke tujuan (multicast)"""
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

    # Forward ke tujuan (B dan C)
    with open(save_path, 'rb') as f:
        data_file = f.read()

    with clients_lock:
        for tujuan in tujuan_list:
            if tujuan in clients:
                try:
                    target_conn = clients[tujuan]
                    # Kirim header ke tujuan
                    header = f"FILE|{nama_pengirim}|{nama_file}|{len(data_file)}\n"
                    target_conn.sendall(header.encode())
                    target_conn.sendall(data_file)
                    print(f"[SERVER] File '{nama_file}' diteruskan ke {tujuan}")
                except Exception as e:
                    print(f"[SERVER] Gagal kirim ke {tujuan}: {e}")
            else:
                print(f"[SERVER] {tujuan} tidak ditemukan / belum konek")

    conn.sendall(b"OK\n")

def handle_client(conn, addr):
    nama = None
    try:
        # Langkah 1: terima nama client
        nama = conn.recv(1024).decode().strip()
        with clients_lock:
            clients[nama] = conn
        print(f"[SERVER] {nama} terhubung dari {addr}")
        conn.sendall(b"TERHUBUNG\n")

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            parts = data.split('|')
            tipe = parts[0]

            # Format: TEKS|pengirim|tujuan1,tujuan2|isi pesan
            if tipe == 'TEKS':
                pengirim = parts[1]
                tujuan_list = parts[2].split(',')
                pesan = parts[3]
                print(f"[SERVER] TEKS dari {pengirim} ke {tujuan_list}: {pesan}")

                with clients_lock:
                    for tujuan in tujuan_list:
                        if tujuan in clients:
                            try:
                                msg = f"TEKS|{pengirim}|{pesan}\n"
                                clients[tujuan].sendall(msg.encode())
                            except Exception as e:
                                print(f"[SERVER] Gagal kirim teks ke {tujuan}: {e}")

                conn.sendall(b"OK\n")

            # Format: FILE|pengirim|tujuan1,tujuan2|nama_file|ukuran
            elif tipe == 'FILE':
                pengirim = parts[1]
                tujuan_list = parts[2].split(',')
                nama_file = parts[3]
                ukuran_file = int(parts[4])
                print(f"[SERVER] FILE dari {pengirim} ke {tujuan_list}: {nama_file} ({ukuran_file} bytes)")
                conn.sendall(b"SIAP\n")
                terima_file(conn, pengirim, nama_file, ukuran_file, tujuan_list)

    except Exception as e:
        print(f"[SERVER] Error dari {nama or addr}: {e}")
    finally:
        if nama:
            with clients_lock:
                clients.pop(nama, None)
            print(f"[SERVER] {nama} disconnect")
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[SERVER] Berjalan di {HOST}:{PORT}")
    print(f"[SERVER] Menunggu koneksi...\n")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    main()