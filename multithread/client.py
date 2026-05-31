import socket
import struct
import os
import threading

SERVER_HOST = '192.168.18.2'
SERVER_PORT = 9999
BUFFER_SIZE = 4096

def build_packet(msg_type: int, payload: bytes) -> bytes:
    """Buat paket: 1 byte tipe + 4 byte panjang payload + payload."""
    header = bytes([msg_type]) + struct.pack("!I", len(payload))
    return header + payload

def send_text(sock, text: str):
    """Kirim pesan teks (kata, kalimat, atau paragraf)."""
    payload = text.encode("utf-8")
    packet = build_packet(1, payload)
    sock.sendall(packet)
    response = sock.recv(BUFFER_SIZE).decode()
    print(f"  [SERVER] {response}")

def send_file(sock, filepath: str):
    """Kirim file apapun: txt, docx, pdf, jpg, png, mp3, mp4, dll."""
    if not os.path.exists(filepath):
        print(f"  [ERROR] File tidak ditemukan: {filepath}")
        return

    filename = os.path.basename(filepath).encode("utf-8")
    with open(filepath, "rb") as f:
        file_data = f.read()

    # Payload: 2 byte panjang nama + nama file + isi file
    name_len = struct.pack("!H", len(filename))
    payload = name_len + filename + file_data

    packet = build_packet(2, payload)
    sock.sendall(packet)
    response = sock.recv(BUFFER_SIZE).decode()
    print(f"  [SERVER] {response}")



def task_kirim_kata(teks, label="Thread-Kata"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[{label}] Mengirim 1-5 kata...")
        send_text(s, teks)

def task_kirim_kalimat(teks, label="Thread-Kalimat"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[{label}] Mengirim 1 kalimat panjang...")
        send_text(s, teks)

def task_kirim_paragraf(teks, label="Thread-Paragraf"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[{label}] Mengirim 1 paragraf...")
        send_text(s, teks)

def task_kirim_file(filepath: str, label="Thread-File"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[{label}] Mengirim file: {filepath}")
        send_file(s, filepath)


def menu():
    print("  UNICAST A -> B  |  Multithread Client")
    print("1. Kirim 1-5 kata")
    print("2. Kirim 1 kalimat panjang")
    print("3. Kirim 1 paragraf")
    print("4. Kirim file dokumen (txt/docx/pdf)")
    print("5. Kirim gambar (JPG/PNG)")
    print("6. Kirim audio MP3")
    print("7. Kirim video MP4")
    print("8. Kirim semua sekaligus (multithread demo)")
    print("0. Keluar")
    return input("Pilih opsi: ").strip()

def main():
    while True:
        pilihan = menu()

        if pilihan == "1":
            teks = input("  Ketik 1-5 kata: ").strip()
            t = threading.Thread(target=task_kirim_kata, args=(teks, "Thread-Kata"))
            t.start(); t.join()

        elif pilihan == "2":
            teks = input("  Ketik 1 kalimat panjang: ").strip()
            t = threading.Thread(target=task_kirim_kalimat, args=(teks, "Thread-Kalimat"))
            t.start(); t.join()

        elif pilihan == "3":
            teks = input("  Ketik 1 paragraf: ").strip()
            t = threading.Thread(target=task_kirim_paragraf, args=(teks, "Thread-Paragraf"))
            t.start(); t.join()

        elif pilihan == "4":
            path = input("  Masukkan path file (txt/docx/pdf): ").strip()
            t = threading.Thread(target=task_kirim_file, args=(path, "Thread-Dokumen"))
            t.start(); t.join()

        elif pilihan == "5":
            path = input("  Masukkan path file gambar (jpg/png): ").strip()
            t = threading.Thread(target=task_kirim_file, args=(path, "Thread-Gambar"))
            t.start(); t.join()

        elif pilihan == "6":
            path = input("  Masukkan path file MP3: ").strip()
            t = threading.Thread(target=task_kirim_file, args=(path, "Thread-MP3"))
            t.start(); t.join()

        elif pilihan == "7":
            path = input("  Masukkan path file MP4: ").strip()
            t = threading.Thread(target=task_kirim_file, args=(path, "Thread-MP4"))
            t.start(); t.join()

        elif pilihan == "8":
            print("\n[DEMO] Menjalankan semua jenis pengiriman secara multithread...")
            kata = input("  Ketik 1-5 kata: ").strip()
            kalimat = input("  Ketik 1 kalimat panjang: ").strip()
            paragraf = input("  Ketik 1 paragraf: ").strip()
            threads = [
                threading.Thread(target=task_kirim_kata,     args=(kata,     "T1-Kata")),
                threading.Thread(target=task_kirim_kalimat,  args=(kalimat,  "T2-Kalimat")),
                threading.Thread(target=task_kirim_paragraf, args=(paragraf, "T3-Paragraf")),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            print("\n[DEMO] Semua thread selesai.")

        elif pilihan == "0":
            print("Keluar. Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()