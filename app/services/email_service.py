from email.message import EmailMessage
import aiosmtplib


async def send_email(to_email: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Your Verification Code"
    msg["From"] = "noreply@melody.com"
    msg["To"] = to_email
    msg.set_content(f"Your verification code is: {code}")

    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username="6351071062@st.utc2.edu.vn",
        password="25/10/2004",
    )
