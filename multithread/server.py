import socket
import threading
import os
import struct

HOST = '0.0.0.0'
PORT = 9999
BUFFER_SIZE = 4096
SAVE_DIR = "received_files"

os.makedirs(SAVE_DIR, exist_ok=True)

def recv_all(sock, length):
    """Terima data sejumlah `length` byte secara lengkap."""
    data = b""
    while len(data) < length:
        packet = sock.recv(min(length - len(data), BUFFER_SIZE))
        if not packet:
            raise ConnectionError("Koneksi terputus sebelum data selesai diterima.")
        data += packet
    return data

def handle_client(conn, addr):
    print(f"\n[+] Client terhubung: {addr}")
    try:
        while True:
            # Terima header: tipe pesan (1 byte) + panjang payload (4 byte)
            header = recv_all(conn, 5)
            msg_type = header[0]
            payload_len = struct.unpack("!I", header[1:5])[0]

            payload = recv_all(conn, payload_len)

            # ---- Tipe 1: Teks (kata / kalimat / paragraf) ----
            if msg_type == 1:
                text = payload.decode("utf-8")
                print(f"[{addr}] Teks diterima: {text}")
                conn.sendall(b"OK: Teks diterima")

            # ---- Tipe 2: File (dokumen, gambar, audio, video) ----
            elif msg_type == 2:
                # Format payload: 2 byte panjang nama file + nama file + isi file
                name_len = struct.unpack("!H", payload[:2])[0]
                filename = payload[2:2 + name_len].decode("utf-8")
                file_data = payload[2 + name_len:]

                save_path = os.path.join(SAVE_DIR, filename)
                with open(save_path, "wb") as f:
                    f.write(file_data)

                size_kb = len(file_data) / 1024
                print(f"[{addr}] File diterima: '{filename}' ({size_kb:.1f} KB) -> disimpan di '{save_path}'")
                conn.sendall(f"OK: File '{filename}' diterima ({size_kb:.1f} KB)".encode())

            else:
                print(f"[{addr}] Tipe pesan tidak dikenal: {msg_type}")
                conn.sendall(b"ERROR: Tipe pesan tidak dikenal")

    except ConnectionError as e:
        print(f"[-] Client {addr} terputus: {e}")
    except Exception as e:
        print(f"[!] Error dari {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Koneksi dengan {addr} ditutup.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[SERVER] Berjalan di {HOST}:{PORT} — menunggu koneksi...")
    print(f"[SERVER] File yang diterima akan disimpan di folder: '{SAVE_DIR}/'")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()
        print(f"[SERVER] Total thread aktif: {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()