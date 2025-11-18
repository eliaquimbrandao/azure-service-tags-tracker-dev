"""
Email Service using SendGrid
Handles sending confirmation and notification emails.
"""

import os
from typing import Dict, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """Email service for subscription management"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@azure-tracker.com')
        self.from_name = os.getenv('FROM_NAME', 'Azure Service Tags Tracker')
        self.app_url = os.getenv('APP_URL', 'https://eliaquimbrandao.github.io/azure-service-tags-tracker')
        self.client = None
        
        if self.api_key and self.api_key != 'your_sendgrid_api_key_here':
            self.client = SendGridAPIClient(self.api_key)
    
    def send_confirmation_email(self, subscription: Dict) -> bool:
        """
        Send subscription confirmation email
        
        Args:
            subscription: Subscription data with email, id, token
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            print("⚠️ SendGrid not configured. Email would be sent to:", subscription['email'])
            self._log_email_to_console(subscription)
            return False
        
        try:
            unsubscribe_url = f"{self.app_url}/unsubscribe.html?token={subscription['unsubscribe_token']}&email={subscription['email']}"
            
            # Prepare email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📧 Subscription Confirmed!</h1>
                    </div>
                    <div class="content">
                        <p>Thank you for subscribing to Azure Service Tags updates!</p>
                        
                        <p><strong>Your Subscription Details:</strong></p>
                        <ul>
                            <li>Email: {subscription['email']}</li>
                            <li>Type: {subscription.get('subscriptionType', 'all').title()} Changes</li>
                            <li>Subscribed: {subscription['timestamp']}</li>
                        </ul>
                        
                        <p>You'll receive email notifications when Azure IP ranges and Service Tags change.</p>
                        
                        <div class="footer">
                            <p>Don't want these emails anymore?</p>
                            <p><a href="{unsubscribe_url}">Unsubscribe</a></p>
                            <p style="margin-top: 20px;">Azure Service Tags Tracker<br>
                            Automated monitoring powered by GitHub Actions</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(subscription['email']),
                subject='✅ Azure Service Tags Subscription Confirmed',
                html_content=Content("text/html", html_content)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Confirmation email sent to {subscription['email']}")
                return True
            else:
                print(f"⚠️ Email send failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def send_change_notification(self, recipients: List[str], changes: Dict) -> bool:
        """
        Send notification email about Azure Service Tags changes
        
        Args:
            recipients: List of email addresses
            changes: Change data from latest-changes.json
        
        Returns:
            True if sent successfully
        """
        if not self.client:
            print(f"⚠️ SendGrid not configured. Would send to {len(recipients)} recipients")
            return False
        
        try:
            # Prepare change summary
            total_changes = len(changes.get('changes', []))
            timestamp = changes.get('timestamp', 'Unknown')
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; }}
                    .change-item {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 4px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔔 Azure Service Tags Updated!</h1>
                    </div>
                    <div class="content">
                        <p><strong>{total_changes}</strong> services have been updated.</p>
                        <p><strong>Detected:</strong> {timestamp}</p>
                        
                        <a href="{self.app_url}" class="button">View Full Details</a>
                        
                        <div class="footer">
                            <p>You're receiving this because you subscribed to Azure Service Tags updates.</p>
                            <p><a href="{self.app_url}/unsubscribe.html">Manage Subscription</a></p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send to all recipients (batch send)
            for email in recipients:
                message = Mail(
                    from_email=Email(self.from_email, self.from_name),
                    to_emails=To(email),
                    subject=f'🔔 Azure Service Tags Updated - {total_changes} Changes Detected',
                    html_content=Content("text/html", html_content)
                )
                
                self.client.send(message)
            
            print(f"✅ Change notifications sent to {len(recipients)} subscribers")
            return True
            
        except Exception as e:
            print(f"❌ Error sending notifications: {e}")
            return False
    
    def _log_email_to_console(self, subscription: Dict):
        """Log email content to console for development"""
        unsubscribe_url = f"{self.app_url}/unsubscribe.html?token={subscription['unsubscribe_token']}&email={subscription['email']}"
        
        print("\n" + "="*60)
        print("📧 CONFIRMATION EMAIL (Development Mode)")
        print("="*60)
        print(f"To: {subscription['email']}")
        print(f"Subject: ✅ Azure Service Tags Subscription Confirmed")
        print(f"\nYou've successfully subscribed to Azure Service Tags updates!")
        print(f"Type: {subscription.get('subscriptionType', 'all').title()} Changes")
        print(f"\nUnsubscribe: {unsubscribe_url}")
        print("="*60 + "\n")
