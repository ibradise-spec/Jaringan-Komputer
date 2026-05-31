import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5000
BUFFER_SIZE = 4096
SAVE_DIR = 'received_files'

def terima_pesan(conn):
    """Thread untuk menerima pesan/file dari server (mode penerima)"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    while True:
        try:
            header = b""
            while not header.endswith(b"\n"):
                byte = conn.recv(1)
                if not byte:
                    return
                header += byte

            header = header.decode().strip()
            if not header:
                continue

            parts = header.split('|')
            tipe = parts[0]

            if tipe == 'TEKS':
                pengirim = parts[1]
                pesan = parts[2]
                print(f"\n[PESAN MASUK] Dari {pengirim}: {pesan}")
                print(">> ", end='', flush=True)

            elif tipe == 'FILE':
                pengirim = parts[1]
                nama_file = parts[2]
                ukuran = int(parts[3])

                print(f"\n[FILE MASUK] Dari {pengirim}: {nama_file} ({ukuran} bytes)")

                save_path = os.path.join(SAVE_DIR, f"dari_{pengirim}_{nama_file}")
                diterima = 0
                with open(save_path, 'wb') as f:
                    while diterima < ukuran:
                        sisa = ukuran - diterima
                        chunk = conn.recv(min(BUFFER_SIZE, sisa))
                        if not chunk:
                            break
                        f.write(chunk)
                        diterima += len(chunk)

                print(f"[FILE] Disimpan di: {save_path}")
                print(">> ", end='', flush=True)

        except Exception as e:
            print(f"\n[CLIENT] Koneksi terputus: {e}")
            break

def kirim_file(conn, nama_saya, tujuan_list, path_file):
    """Kirim file ke server untuk di-multicast"""
    if not os.path.exists(path_file):
        print(f"[ERROR] File tidak ditemukan: {path_file}")
        return

    nama_file = os.path.basename(path_file)
    ukuran = os.path.getsize(path_file)
    tujuan_str = ','.join(tujuan_list)

    # Kirim header
    header = f"FILE|{nama_saya}|{tujuan_str}|{nama_file}|{ukuran}\n"
    conn.sendall(header.encode())

    # Tunggu konfirmasi server siap
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    resp = resp.decode().strip()

    if resp != "SIAP":
        print(f"[ERROR] Server tidak siap: {resp}")
        return

    # Kirim file
    print(f"[CLIENT] Mengirim file '{nama_file}' ({ukuran} bytes)...")
    with open(path_file, 'rb') as f:
        terkirim = 0
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)
            terkirim += len(chunk)
            persen = (terkirim / ukuran) * 100
            print(f"\r[CLIENT] Progress: {persen:.1f}%", end='', flush=True)

    # Tunggu konfirmasi OK
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print(f"\n[CLIENT] File berhasil dikirim!")

def kirim_teks(conn, nama_saya, tujuan_list, pesan):
    """Kirim teks ke server untuk di-multicast"""
    tujuan_str = ','.join(tujuan_list)
    msg = f"TEKS|{nama_saya}|{tujuan_str}|{pesan}\n"
    conn.sendall(msg.encode())

    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print("[CLIENT] Pesan terkirim!")

def menu_pengirim(conn, nama_saya, tujuan_list):
    """Menu untuk pengirim (Client A)"""
    print(f"\n[MODE PENGIRIM] Kamu: {nama_saya} | Tujuan: {', '.join(tujuan_list)}")

    while True:
        print("\n===== MENU MULTICAST =====")
        print("1. Kirim dokumen (txt, docx, pdf)")
        print("2. Kirim gambar (jpg, png)")
        print("3. Kirim suara (mp3)")
        print("4. Kirim video (mp4)")
        print("5. Keluar")
        pilihan = input(">> Pilih: ").strip()

        if pilihan == '1':
            path = input("Masukkan path file dokumen (txt/docx/pdf): ").strip()
            kirim_file(conn, nama_saya, tujuan_list, path)

        elif pilihan == '2':
            path = input("Masukkan path file gambar (jpg/png): ").strip()
            kirim_file(conn, nama_saya, tujuan_list, path)

        elif pilihan == '3':
            path = input("Masukkan path file audio (mp3): ").strip()
            kirim_file(conn, nama_saya, tujuan_list, path)

        elif pilihan == '4':
            path = input("Masukkan path file video (mp4): ").strip()
            kirim_file(conn, nama_saya, tujuan_list, path)

        elif pilihan == '5':
            print("[CLIENT] Keluar...")
            break

        else:
            print("[ERROR] Pilihan tidak valid!")

def main():
    print("===== CLIENT MULTICAST =====")
    nama_saya = input("Masukkan nama kamu (A/B/C): ").strip()

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))

    # Kirim nama ke server
    conn.sendall((nama_saya + '\n').encode())

    # Tunggu konfirmasi
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print(f"[CLIENT] {resp.decode().strip()}")

    # Pilih mode
    print("\nPilih mode:")
    print("1. Pengirim (A) - kirim file/pesan")
    print("2. Penerima (B atau C) - tunggu file/pesan")
    mode = input(">> Pilih: ").strip()

    if mode == '1':
        tujuan_input = input("Masukkan nama tujuan (pisah koma, contoh: B,C): ").strip()
        tujuan_list = [t.strip() for t in tujuan_input.split(',')]
        menu_pengirim(conn, nama_saya, tujuan_list)

    elif mode == '2':
        print(f"[CLIENT] Mode penerima aktif. Menunggu pesan/file...")
        terima_thread = threading.Thread(target=terima_pesan, args=(conn,))
        terima_thread.daemon = True
        terima_thread.start()
        terima_thread.join()

    conn.close()

if __name__ == '__main__':
    main()