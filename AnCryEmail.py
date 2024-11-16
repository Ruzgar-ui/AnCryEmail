###################
#!      AnCryEmail#
#Coder: Ruzgar-ui #
###################
import email
import imaplib
import os
from email.header import decode_header
from sys import stdout
from time import sleep

gelen_kutusu = "gelen_kutusu.txt"
kullanıcılar = "kullanıcılar.txt"

def get_email_credentials():
    # E-posta bilgilerini al
    text = 'Ankara üniversitesi mail adresinizi giriniz.\nÖrnek: öğrenci_numarası@ogrenci.ankara.edu.tr'
    passwd = 'Mail adresinizin şifresini giriniz.\nŞifreniz yoksa şifre almak için: https://kds.ankara.edu.tr/'
    speed = 0.04
    for char in text:
        stdout.write(f"{char}")
        stdout.flush()
        sleep(speed)
    username = input("\n-->")
    for char in passwd:
        stdout.write(f"{char}")
        stdout.flush()
        sleep(speed)
    password = input("\n-->")
    return username, password

def connect_to_mail_server():
    # IMAP sunucusuna bağlan
    mail = imaplib.IMAP4_SSL("80.251.40.61", 993)

    # Kayıtlı hesapları göster
    if os.path.exists(kullanıcılar):
        with open(kullanıcılar, 'r') as file:
            accounts = file.readlines()
            if accounts:
                print("Kayıtlı Hesaplar:")
                for i, account in enumerate(accounts, 1):
                    username, password = account.strip().split(',')
                    print(f"Hesap {i}: Kullanıcı Adı: {username}, Şifre: {password}")
                action = input("\nFarklı hesaba giriş yapmak için 'y', kayıtlı hesaba giriş yapmak için 'g' yazın: ").lower()
                if action == 'g':
                    try:
                        choice = int(input("\nBir hesap seçin (1, 2, ...): "))
                        if 1 <= choice <= len(accounts):
                            username, password = accounts[choice - 1].strip().split(',')
                            mail.login(username, password)
                            print("Mail sunucusuna bağlanıldı.")
                            return mail
                        else:
                            print("Geçersiz seçim. Lütfen geçerli bir hesap numarası girin.")
                    except ValueError:
                        print("Lütfen geçerli bir sayı girin.")
                elif action == 'y':
                    username, password = get_email_credentials()
                else:
                    print("Geçersiz seçenek!")
            else:
                print("Kayıtlı mail hesabı bulunamadı.")
                username, password = get_email_credentials()
    else:
        print("Kayıtlı mail hesap dosyası bulunamadı.")
        username, password = get_email_credentials()
    try:
        mail.login(username, password)
        print("Mail sunucusuna bağlanıldı.")
        # Hesabı dosyaya kaydet
        with open(kullanıcılar, 'a') as file:
            file.write(f"{username},{password}\n")
        print(f"{username} hesabı kaydedildi.")
    except:
        print("Sunucuya bağlanma başarısız oldu.\nLütfen mail adresinizi ve şifrenizi kontrol ediniz.")
        return None
    return mail

def check_mail_count(mail):
    """Gelen kutusundaki mesaj sayısını al."""
    # 'inbox' (gelen kutusu) klasörünü seç
    mail.select("inbox")
    
    # Tüm mesajların kimliklerini al (mesajlar okunmuş veya okunmamış olabilir)
    status, messages = mail.search(None, "ALL")
    if status == "OK":
        # Mesajların kimliklerinin sayısını yazdır
        message_ids = messages[0].split()
        print(f"Gelen kutusunda {len(message_ids)} mesaj var.")
        return message_ids  # Mesaj ID'lerini gönder
    else:
        print("Mesajları almakta sorun oluştu.")
        return []

def get_message_content(mail, msg_id):
    """Mesajın içeriğini al."""
    status, msg_data = mail.fetch(msg_id, "(RFC822)")
    if status == "OK":
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Mesajı çözümle
                msg = email.message_from_bytes(response_part[1])
                
                # Mesaj başlığını tanımla (Konu, Gönderen)
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                from_ = msg.get("From")
                
                # Mesajın içeriğini al
                body = ""
                if msg.is_multipart():
                    # Mesaj multipart ise her parçayı oku
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        # Eğer içerik bir metinse, al
                        if "attachment" not in content_disposition:
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            elif content_type == "text/html":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                else:
                    # Eğer mesaj multipart değilse, doğrudan içerik al
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                
                return subject, from_, body
    return None, None, None

def mark_as_read(mail, message_ids):
    """Okunmuş mesajları işaretle ve kaydet."""
    # Önceden kaydedilen okunmuş mail ID'lerini oku
    read_mail_ids = read_read_mail_ids_from_file()

    for msg_id in message_ids:
        # Eğer mesaj zaten okunmuşsa, dosyaya kaydet ve ekrana yaz
        if msg_id.decode("utf-8") in read_mail_ids:
            print(f"Mesaj {msg_id.decode('utf-8')} zaten okundu.")
            continue
        
        # Mesajı okundu olarak işaretle
        mail.store(msg_id, '+FLAGS', '\\Seen')
        print(f"Mesaj {msg_id.decode('utf-8')} okunmuş olarak işaretlendi.")
        
        # Mesajın içeriğini al
        subject, from_, body = get_message_content(mail, msg_id)
        
        if subject and from_ and body:
            # İçeriği dosyaya kaydet ve ekrana yazdır
            save_read_mail_id_to_file(msg_id, subject, from_, body)
            print_mail_info(msg_id, subject, from_, body)  # Ekrana yazdır

def save_read_mail_id_to_file(msg_id, subject, from_, body):
    """Okunmuş mail ID'sini ve içeriğini dosyaya kaydet."""
    with open(gelen_kutusu, "a", encoding="utf-8") as f:
        f.write(f"ID: {msg_id.decode('utf-8')}\n")
        f.write(f"Subject: {subject}\n")
        f.write(f"From: {from_}\n")
        f.write(f"Body:\n{body}\n\n" + "="*50 + "\n")

def print_mail_info(msg_id, subject, from_, body):
    """Mesajın bilgilerini ekrana yazdır."""
    print(f"ID: {msg_id.decode('utf-8')}")
    print(f"Subject: {subject}")
    print(f"From: {from_}")
    print(f"Body:\n{body}")
    print("="*50)

def read_read_mail_ids_from_file():
    """Dosyadan okunmuş mail ID'lerini oku."""
    if not os.path.exists(gelen_kutusu):
        return []
    
    with open(gelen_kutusu, "r", encoding="utf-8") as f:
        return [line.split(": ")[1].strip() for line in f.readlines() if line.startswith("ID: ")]

def main():
    # E-posta sunucusuna bağlan
    mail = connect_to_mail_server()
    message_ids = None

    # Mesajların kimliklerini al
    if mail is not None:
        message_ids = check_mail_count(mail)
    
    # Mesajları okundu olarak işaretle ve dosyaya kaydet
    if 'message_ids' in locals() and message_ids:
        mark_as_read(mail, message_ids)
    
    # Çıkış yap
    if mail is not None:
        mail.logout()

if __name__ == "__main__":
    main()
# Her yeni mail geldiğinde yazdıracak bildirim verip terminale yazdıracak
# Terminalden cevap verilebilecek
