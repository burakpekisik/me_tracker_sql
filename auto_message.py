import os
import fnmatch
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
from userInfo import sender_email_auto, sender_password_auto

async def send_mail_to_new_customer(recipient_email):
    sender_email = sender_email_auto
    sender_password = sender_password_auto
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    subject = "Mektup Evi'ne Hoşgeldiniz!"
    keyword = "Kampanya"
    campaign_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        for filename in fnmatch.filter(files, f"*{keyword}*"):
            campaign_files.append(os.path.join(root, filename))
    try:
        f = open("CampaignMessage.txt", "r", encoding="utf-8")
        mailMessage = f.read()
    except Exception as e:
        print("Mail Gönderiminde Hata oluştu 1: ", e)
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(mailMessage, 'plain'))
        for img_path in campaign_files:
            img_name = os.path.basename(img_path)
            with open(img_path, "rb") as img_file:
                img_data = img_file.read()
                img = MIMEImage(img_data, name=img_name)
                msg.attach(img)
        
        async with asyncio.Semaphore(10):  # Limit concurrent connections if necessary
            loop = asyncio.get_event_loop()
            smtp_client = smtplib.SMTP(smtp_server, smtp_port)
            smtp_client.starttls()
            smtp_client.login(sender_email, sender_password)
            await loop.run_in_executor(None, smtp_client.sendmail, sender_email, [recipient_email], msg.as_string())
            smtp_client.quit()
            print(f"E-posta {recipient_email} adresine gönderildi.")
    except Exception as e:
        print("Mail Gönderiminde Hata oluştu 2:", e)