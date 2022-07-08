import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

context = ssl.create_default_context()

def send_mail(fname, smtp_server, port, from_addr, from_password, to_addr, convert=False):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = 'convert' if convert else ''
    msg.attach(MIMEText('bkmgr: Syncing e-book to Kindle device.', 'plain'))

    with open(fname, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {fname}",
    )
    msg.attach(part)

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.ehlo()
        server.login(from_addr, from_password)
        server.sendmail(from_addr, to_addr, msg.as_string())
