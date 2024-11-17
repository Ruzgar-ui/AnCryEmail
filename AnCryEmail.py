###################
#!      AnCryEmail#
#Coder: Ruzgar-ui #
###################
import email
import imaplib
import os
import smtplib
#import webbrowser
from email.header import decode_header
from sys import stdout
from time import sleep

import colorama
from win10toast import ToastNotifier

gelen_kutusu = "gelen_kutusu.txt"
kullanıcılar = "kullanıcılar.txt"

cyan="\033[96m"
purple="\033[95m"
blue="\033[94m"
green="\033[92m"
red="\033[91m"
reset="\033[00m"

colorama.init()

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
                    print(f"{blue}Hesap {i}: {red}Kullanıcı Adı:{green} {username},{red} Şifre:{green} {password}")
                print(f"\n{cyan}Farklı hesaba giriş yapmak için 'y', kayıtlı hesaba giriş yapmak için 'g' yazın:{reset} ", end="")
                action = input("")
                if action == 'g':
                    try:
                        print(f"{blue}", end="")
                        choice = int(input("\nBir hesap seçin (1, 2, ...): "))
                        if 1 <= choice <= len(accounts):
                            username, password = accounts[choice - 1].strip().split(',')
                            mail.login(username, password)
                            print(f"Mail sunucusuna bağlanıldı.{green}")
                            return mail, username, password
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
        print(f"{blue}Mail sunucusuna bağlanıldı.{green}")
        # Hesabı dosyaya kaydet
        with open(kullanıcılar, 'a') as file:
            file.write(f"{username},{password}\n")
        print(f"{username} hesabı kaydedildi.")
    except:
        print("Sunucuya bağlanma başarısız oldu.\nLütfen mail adresinizi ve şifrenizi kontrol ediniz.")
        return None
    return mail, username, password

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
    if subject and msg_id and from_ and body:
    # tarayıcıda mailleri görmek için kaydet
        folder_name = "".join(c if c.isalnum() else "_" for c in subject)
        if not os.path.isdir(folder_name):
            # index.html dosyasını oluştur
            os.mkdir(folder_name)
        filename = "index.html"
        filepath = os.path.join(folder_name, filename)
        # Dosyaya yaz
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
        except Exception as e:
            print(f"Dosya açılamadı: {e}")
    with open(gelen_kutusu, "a", encoding="utf-8") as f:
        f.write(f"ID: {msg_id.decode('utf-8')}\n")
        f.write(f"Konu: {subject}\n")
        f.write(f"Kimden: {from_}\n")
        f.write(f"Mesaj içeriği:\n{body}\n\n" + "="*50 + "\n")
    #webbrowser.open(filepath)

def print_mail_info(msg_id, subject, from_, body):
    """Mesajın bilgilerini ekrana yazdır."""
    print(f"ID: {msg_id.decode('utf-8')}")
    print(f"Konu: {subject}")
    print(f"Kimden: {from_}")
    print(f"Mesaj içeriği:\n{body}")
    print("="*50)

def read_read_mail_ids_from_file():
    """Dosyadan okunmuş mail ID'lerini oku."""
    if not os.path.exists(gelen_kutusu):
        return []
    
    with open(gelen_kutusu, "r", encoding="utf-8") as f:
        return [line.split(": ")[1].strip() for line in f.readlines() if line.startswith("ID: ")]

def new_mails(mail):
    try:
        print(f"{red}Yeni E-mail gelmesini burada bekleyeceğim...\n{green}[{red}-{green}]{reset} ", end="")
        while True:
            # Gelen kutusundaki yeni mailleri kontrol et
            status, messages = mail.search(None, 'UNSEEN')  # 'UNSEEN' sadece okunmamış mailleri getirir
            message_ids = messages[0].split()
            mark_as_read(mail, message_ids)
            if status == "OK":
                # Yeni gelen e-postaların ID'lerini al
                for msg_id in messages[0].split():
                    # E-posta içeriğini al
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            # E-posta mesajını parse et
                            msg = email.message_from_bytes(response_part[1])
                            
                            # E-posta başlıklarını al
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                # Eğer başlık bytes olarak gelirse, decode et
                                subject = subject.decode(encoding if encoding else "utf-8")
                            from_ = msg.get("From")
                            
                            my_notification = ToastNotifier()
                            my_notification.show_toast("Yeni E-posta!", f"{from_} sana bir mail gönderdi.")
                            print(f"Yeni e-posta geldi!")
                            print(f"Kimden: {from_}")
                            print(f"Konu: {subject}")
                            
                            # Eğer e-posta birden fazla parçada oluşuyorsa
                            if msg.is_multipart():
                                for part in msg.walk():
                                    # E-posta metni
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    if "attachment" not in content_disposition:
                                        if content_type == "text/plain":
                                            body = part.get_payload(decode=True).decode()
                                            print(f"Mesaj içeriği: {body}\n")
                            else:
                                # Eğer tek parça bir mesaj ise
                                body = msg.get_payload(decode=True).decode()
                                print(f"Mesaj içeriği: {body}\n")
            # 10 saniyede bir kontrol et
            sleep(10)
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

def send_mails(username, password):
    # E-posta başlıkları ve içeriği
    print(f"{cyan}Kimden:{red} {username}")
    print(f"{cyan}Kime: {red}", end="")
    receiver_mail = input("")
    print(f"{cyan}Başlık: {red}", end="")
    subject = input("")
    print(f"{cyan}Mesaj: {red}", end="")
    body = input("")
    print(f"{reset}", end="")

    # E-posta başlıklarını ve içeriğini birleştirme
    message = f"From: {username}\r\n"
    message += f"To: {receiver_mail}\r\n"
    message += f"Subject: {subject}\r\n"
    message += f"\r\n"  # Başlık ve içerik arasındaki boş satır
    message += body
    message = message.encode('utf-8')
    # SMTP sunucusuna bağlanma ve e-posta gönderme
    try:
        # SSL bağlantısını başlat
        server = smtplib.SMTP_SSL('80.251.40.61', 465)

        # Gmail hesabına giriş yap
        server.login(username, password)

        # E-posta gönder
        server.sendmail(username, receiver_mail, message)
        print(f"{purple}E-posta başarıyla gönderildi!{reset}")

    except Exception as e:
        print(f"Hata oluştu: {e}")
        print(f"{red}Girdiğiniz mail adresiniz kontrol edin!{reset}")

    finally:
        server.quit()  # Bağlantıyı kapat

def main():
    # E-posta sunucusuna bağlan
    mail, username, password = connect_to_mail_server()
    message_ids = None

    # Mesajların kimliklerini al
    if mail is not None:
        message_ids = check_mail_count(mail)
    
    # Mesajları okundu olarak işaretle ve dosyaya kaydet
    if 'message_ids' in locals() and message_ids:
        mark_as_read(mail, message_ids)
    
    try:
        while True:
            print(f"""{green}
    #########################################
    ##                                     ##
    ##   {red}1-) Mail göndermek istiyorum.   {green}  ##
    ##   {red}2-) Mail gelirse bana haber ver.{green}  ##
    ##   {red}3-) Çıkış yap.                  {green}  ##
    ##                                     ##
    #########################################
            """)
            print(f"\n{green}[{red}*{green}]{reset} ", end="")
            choice = input("")
            # Mail gönder
            if int(choice) == 1 and True and mail is not None:
                send_mails(username, password)
            # Yeni mail gelmesini bekle
            elif int(choice) == 2 and True and mail is not None:
                new_mails(mail)
            elif int(choice) == 3 and True and mail is not None:
                print("Çıkış yapılıyor...")
                break
            else:
                print("Hatalı seçim yaptınız.")
    except Exception as e:
        print(f"Hata ile karşılaşıldı: {e}")

    # Çıkış yap
    if mail is not None:
        mail.logout()

if __name__ == "__main__":
    main()
