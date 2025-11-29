import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

from api.database import player_database, binds
from api.misc import generate_otp, check_email

server = None

def init_email():
    print("[SMTP] Initializing email server...")
    global server
    if SMTP_PORT == 25 or SMTP_PORT == 80:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    else:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)

    server.ehlo()
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("[SMTP] Email server initialized successfully.")

async def send_email(to_addr, code, lang):
    global server
    title = {"en": "Project Taiyo - Email Verification", "zh": "项目 Taiyo - 邮件验证", "tc": "專案 Taiyo - 郵件驗證", "jp": "プロジェクト Taiyo - メール認証"}
    with open(f"web/email_{lang}.html", "r", encoding="utf-8") as file:
        body = file.read()

    body = body.format(code=code)

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_addr
    msg['Subject'] = title.get(lang, title['en'])

    msg.attach(MIMEText(body, 'html'))

    try:
        server.sendmail(SMTP_USER, to_addr, msg.as_string())
        print("Email sent to ", to_addr)
    except Exception as e:
        print(f"Email error: {e}")

async def send_email_to_user(email, user_id):
    if not email or not check_email(email):
        return "Invalid Email."
    
    verify = await player_database.fetch_one(binds.select().where(binds.c.bind_acc == email))
    if verify:
        if (datetime.utcnow() - verify['bind_date']).total_seconds() < 60:
            return "Too many requests. Please try again later."

    verify_code, hash_code = generate_otp()
    try:
        await send_email(email, verify_code, "en")
        if verify:
            await player_database.execute(binds.update().where(binds.c.user_id == user_id).values(
                bind_acc=email,
                bind_code=verify_code,
                bind_date=datetime.utcnow()
            ))
        else:
            query = binds.insert().values(
                user_id=user_id,
                bind_acc=email,
                bind_code=verify_code,
                is_verified=0,
                bind_date=datetime.utcnow()
            )
            await player_database.execute(query)

        return "Email sent. Please enter the page again, fill in the verification code to complete the binding."

    except Exception as e:
        print(f"Email error: {e}")
        return "Failed to send email. Please try again later."