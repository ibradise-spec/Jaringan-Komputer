import socket
import os
import struct

SERVER_HOST = '127.0.0.1'  # Ganti dengan IP Server jika beda mesin
SERVER_PORT = 9999
BUFFER_SIZE = 4096

def send_text(sock, text):
    """Kirim teks dengan header 4-byte panjang."""
    encoded = text.encode('utf-8')
    sock.sendall(struct.pack('>I', len(encoded)))
    sock.sendall(encoded)


def send_file(sock, filepath):
    """Kirim file dengan header nama + ukuran."""
    filename = os.path.basename(filepath)
    name_bytes = filename.encode('utf-8')
    file_size = os.path.getsize(filepath)

    sock.sendall(struct.pack('>I', len(name_bytes)))
    sock.sendall(name_bytes)
    sock.sendall(struct.pack('>Q', file_size))
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)
    return filename, file_size


def print_menu():
    print("\n" + "=" * 52)
    print("   CLIENT (A) - UNICAST SINGLE THREAD")
    print("=" * 52)
    print("  [1] Kirim 1-5 kata")
    print("  [2] Kirim 1 kalimat panjang")
    print("  [3] Kirim 1 paragraf")
    print("  [4] Kirim dokumen (txt/docx/pdf)")
    print("  [5] Kirim gambar (JPG/PNG)")
    print("  [6] Kirim suara (mp3)")
    print("  [7] Kirim video (mp4)")
    print("  [0] Keluar")
    print("-" * 52)


def kirim_kata(sock):
    teks = input("  Masukkan 1-5 kata: ").strip()
    words = teks.split()
    if not (1 <= len(words) <= 5):
        print("  [!] Harus 1 sampai 5 kata!")
        return
    sock.sendall(bytes([1]))
    send_text(sock, teks)
    print(f"  [v] Terkirim: '{teks}'")

def kirim_kalimat(sock):
    teks = input("  Masukkan 1 kalimat panjang: ").strip()
    if not teks:
        print("  [!] Kalimat tidak boleh kosong!")
        return
    sock.sendall(bytes([2]))
    send_text(sock, teks)
    print(f"  [v] Terkirim.")

def kirim_paragraf(sock):
    print("  Masukkan paragraf (akhiri dengan baris kosong):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    teks = " ".join(lines)
    if not teks:
        print("  [!] Paragraf tidak boleh kosong!")
        return
    sock.sendall(bytes([3]))
    send_text(sock, teks)
    print(f"  [v] Paragraf terkirim ({len(teks)} karakter)")

def kirim_dokumen(sock):
    path = input("  Path file dokumen (txt/docx/pdf): ").strip()
    if not os.path.isfile(path):
        print(f"  [!] File tidak ditemukan: {path}")
        return
    ext = os.path.splitext(path)[1].lower()
    if ext not in ['.txt', '.docx', '.pdf']:
        print("  [!] Ekstensi harus .txt, .docx, atau .pdf")
        return
    sock.sendall(bytes([4]))
    filename, size = send_file(sock, path)
    print(f"  [v] Dokumen '{filename}' terkirim ({size} bytes)")

def kirim_gambar(sock):
    path = input("  Path file gambar (JPG/PNG): ").strip()
    if not os.path.isfile(path):
        print(f"  [!] File tidak ditemukan: {path}")
        return
    ext = os.path.splitext(path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        print("  [!] Ekstensi harus .jpg, .jpeg, atau .png")
        return
    sock.sendall(bytes([5]))
    filename, size = send_file(sock, path)
    print(f"  [v] Gambar '{filename}' terkirim ({size} bytes)")

def kirim_suara(sock):
    path = input("  Path file suara (mp3): ").strip()
    if not os.path.isfile(path):
        print(f"  [!] File tidak ditemukan: {path}")
        return
    if not path.lower().endswith('.mp3'):
        print("  [!] Ekstensi harus .mp3")
        return
    sock.sendall(bytes([6]))
    filename, size = send_file(sock, path)
    print(f"  [v] Suara '{filename}' terkirim ({size} bytes)")

def kirim_video(sock):
    path = input("  Path file video (mp4): ").strip()
    if not os.path.isfile(path):
        print(f"  [!] File tidak ditemukan: {path}")
        return
    if not path.lower().endswith('.mp4'):
        print("  [!] Ekstensi harus .mp4")
        return
    sock.sendall(bytes([7]))
    filename, size = send_file(sock, path)
    print(f"  [v] Video '{filename}' terkirim ({size} bytes)")


ACTIONS = {
    '1': kirim_kata,
    '2': kirim_kalimat,
    '3': kirim_paragraf,
    '4': kirim_dokumen,
    '5': kirim_gambar,
    '6': kirim_suara,
    '7': kirim_video,
}


def start_client():
    print(f"\n[*] Menghubungkan ke {SERVER_HOST}:{SERVER_PORT} ...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print("[v] Terhubung!\n")
        with sock:
            while True:
                print_menu()
                pilihan = input("  Pilihan kamu: ").strip()
                if pilihan == '0':
                    sock.sendall(bytes([0xFF]))
                    print("\n[v] Koneksi ditutup. Sampai jumpa!\n")
                    break
                action = ACTIONS.get(pilihan)
                if action:
                    action(sock)
                else:
                    print("  [!] Pilihan tidak valid.")
    except ConnectionRefusedError:
        print(f"\n[x] Gagal terhubung! Pastikan server sudah jalan di {SERVER_HOST}:{SERVER_PORT}")
    except ConnectionError as e:
        print(f"\n[x] Koneksi terputus: {e}")


if __name__ == "__main__":
    start_client()