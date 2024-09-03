import smtplib
from email.mime.text import MIMEText

def send_test_email():
    smtp_server = "smtp.mail.yahoo.com"
    smtp_port = 587
    smtp_user = "twenty8cows.contact@yahoo.com"
    smtp_password = ")Y6Xe3w&*Q8)8@v"

    sender = smtp_user
    recipient = 'twenty8cows@gmail.com'
    subject = 'Test Email'
    body = "Testing 123!"

    msg = MIMEText(body)
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender, recipient, msg.as_string())
            print("Test email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_test_email()
