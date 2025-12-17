import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import Config

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.username = Config.SMTP_USERNAME
        self.password = Config.SMTP_PASSWORD
        self.from_email = Config.FROM_EMAIL

    def send_license_email(self, to_email, license_key, customer_name="Customer"):
        """Send license key to customer via email"""
        if not self.username or not self.password:
            logger.warning("Email credentials not configured. Skipping email send.")
            logger.info(f"Would have sent license {license_key} to {to_email}")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Your ImageWave Converter License"

            body = f"""
Hello {customer_name},

Thank you for purchasing ImageWave Converter!

Here is your license key:
{license_key}

Instructions:
1. Open ImageWave Converter
2. Enter your email: {to_email}
3. Enter the license key above
4. Click Login

If you have any questions, please reply to this email.

Best regards,
The ImageWave Team
"""
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"License email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_trial_email(self, to_email, license_key):
        """Send trial activation email to user"""
        if not self.username or not self.password:
            logger.warning("Email credentials not configured. Skipping trial email send.")
            logger.info(f"Would have sent trial license {license_key} to {to_email}")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "🎁 Your ImageWave Free Trial is Ready!"

            body = f"""
Hello,

Congratulations! Your 1-day free trial of ImageWave Converter has been activated! 🎉

Here is your trial license key:
{license_key}

Trial Details:
• Duration: 24 hours from activation
• No credit card required
• Full access to all features
• No installation of additional software needed

How to use your trial:
1. Open ImageWave Converter
2. 
   - Enter your email: {to_email}
   - Enter the license key: {license_key}
   - Click Login
3. Start converting images and videos!

Supported Formats:
• Images: GIF, WebM, WebP, MP4, and more
• Batch processing


After your trial expires:
If you love ImageWave, purchase a full license for unlimited access at:
https://gumroad.com/l/imagewave

Questions? Reply to this email!

Best regards,
The ImageWave Team
"""
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"Trial email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send trial email: {e}")
            return False
