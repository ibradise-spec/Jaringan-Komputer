
import socket
import os
import struct

HOST = '0.0.0.0'   # Terima dari semua interface
PORT = 9999
BUFFER_SIZE = 4096
SAVE_DIR = "client_received"

os.makedirs(SAVE_DIR, exist_ok=True)


def recv_all(conn, length):
    """Terima sejumlah 'length' byte secara pasti."""
    data = b""
    while len(data) < length:
        packet = conn.recv(min(BUFFER_SIZE, length - len(data)))
        if not packet:
            raise ConnectionError("Koneksi terputus saat menerima data.")
        data += packet
    return data


def receive_text(conn):
    raw_len = recv_all(conn, 4)
    msg_len = struct.unpack('>I', raw_len)[0]
    text = recv_all(conn, msg_len).decode('utf-8')
    return text


def receive_file(conn):
    name_len = struct.unpack('>I', recv_all(conn, 4))[0]
    filename = recv_all(conn, name_len).decode('utf-8')
    file_size = struct.unpack('>Q', recv_all(conn, 8))[0]
    file_data = recv_all(conn, file_size)

    save_path = os.path.join(SAVE_DIR, filename)
    with open(save_path, 'wb') as f:
        f.write(file_data)
    return filename, file_size


def handle_type_1(conn):
    text = receive_text(conn)
    print(f"  [TIPE 1] Kata diterima    : '{text}'")

def handle_type_2(conn):
    text = receive_text(conn)
    print(f"  [TIPE 2] Kalimat diterima : '{text}'")

def handle_type_3(conn):
    text = receive_text(conn)
    print(f"  [TIPE 3] Paragraf diterima:\n    {text}")

def handle_type_4(conn):
    filename, size = receive_file(conn)
    print(f"  [TIPE 4] Dokumen diterima : '{filename}' ({size} bytes)")

def handle_type_5(conn):
    filename, size = receive_file(conn)
    print(f"  [TIPE 5] Gambar diterima  : '{filename}' ({size} bytes)")

def handle_type_6(conn):
    filename, size = receive_file(conn)
    print(f"  [TIPE 6] Suara diterima   : '{filename}' ({size} bytes)")

def handle_type_7(conn):
    filename, size = receive_file(conn)
    print(f"  [TIPE 7] Video diterima   : '{filename}' ({size} bytes)")


TYPE_HANDLERS = {
    1: handle_type_1,
    2: handle_type_2,
    3: handle_type_3,
    4: handle_type_4,
    5: handle_type_5,
    6: handle_type_6,
    7: handle_type_7,
}


def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)

    print("=" * 52)
    print("   SERVER (B) - UNICAST SINGLE THREAD")
    print("=" * 52)
    print(f"  Mendengarkan di {HOST}:{PORT} ...")
    print(f"  File disimpan di folder: '{SAVE_DIR}/'")
    print("  Tekan Ctrl+C untuk menghentikan.\n")

    try:
        while True:
            conn, addr = server_sock.accept()
            print(f"\n[+] Koneksi masuk dari {addr[0]}:{addr[1]}")
            try:
                with conn:
                    while True:
                        header = conn.recv(1)
                        if not header:
                            print(f"[-] Koneksi dari {addr[0]} ditutup.\n")
                            break
                        msg_type = header[0]
                        if msg_type == 0xFF:
                            print(f"[v] Client {addr[0]} selesai mengirim.\n")
                            break
                        handler = TYPE_HANDLERS.get(msg_type)
                        if handler:
                            handler(conn)
                        else:
                            print(f"  [!] Tipe tidak dikenal: {msg_type}")
            except ConnectionError as e:
                print(f"[!] Error: {e}\n")
    except KeyboardInterrupt:
        print("\n[x] Server dihentikan.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()