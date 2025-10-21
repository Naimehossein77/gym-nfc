import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "nayeemrocks22@gmail.com"
# Get this from environment variable in production
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "trxg puvx hmxi viuz")

def send_credentials_email(to_email: str, username: str, password: str) -> bool:
    """
    Send login credentials to member's email
    """
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your GYM NFC Login Credentials"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email

        # Create HTML version of the message
        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
              .content {{ padding: 20px; background-color: #f9f9f9; }}
              .credentials {{ background-color: #fff; padding: 15px; margin: 20px 0; border-left: 4px solid #4CAF50; }}
              .footer {{ font-size: 12px; color: #666; margin-top: 20px; text-align: center; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>Welcome to GYM NFC</h2>
              </div>
              <div class="content">
                <p>Hello,</p>
                <p>Your GYM NFC login credentials have been created. Please find your login details below:</p>
                
                <div class="credentials">
                  <p><strong>Username:</strong> {username}</p>
                  <p><strong>Password:</strong> {password}</p>
                </div>

                <p><strong>Important:</strong></p>
                <ul>
                  <li>Please change your password after first login</li>
                  <li>Keep your credentials secure</li>
                  <li>Do not share these credentials with others</li>
                </ul>

                <p>This is strictly against our privacy policy to share these credentials with anyone.</p>
              </div>
              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© GYM NFC. All rights reserved.</p>
              </div>
            </div>
          </body>
        </html>
        """

        # Convert both text and HTML to MIMEText objects and add them to the container
        part2 = MIMEText(html, 'html')
        msg.attach(part2)

        # Create secure SSL/TLS connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Login to the server
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send email
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False