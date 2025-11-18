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
            change_list = changes.get('changes', [])
            total_changes = len(change_list)
            timestamp = changes.get('timestamp', 'Unknown')
            
            # Build HTML table for changes
            changes_html = ""
            for idx, change in enumerate(change_list[:20], 1):  # Limit to first 20 for email
                service_name = change.get('service', 'Unknown')
                added_count = len(change.get('added', []))
                removed_count = len(change.get('removed', []))
                
                changes_html += f"""
                <div class="change-item">
                    <strong>{idx}. {service_name}</strong><br>
                    <span style="color: #10b981;">✅ Added: {added_count} IP ranges</span><br>
                    <span style="color: #ef4444;">❌ Removed: {removed_count} IP ranges</span>
                </div>
                """
            
            if total_changes > 20:
                changes_html += f"""
                <div class="change-item" style="background: #fef3c7; border-left-color: #f59e0b;">
                    <strong>⚠️ And {total_changes - 20} more services...</strong><br>
                    <a href="{self.app_url}/history.html">View all changes on the dashboard</a>
                </div>
                """
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                    .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 14px; }}
                    .content {{ padding: 30px; }}
                    .summary {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                    .summary h2 {{ margin: 0 0 15px 0; font-size: 18px; color: #0c4a6e; }}
                    .summary-stats {{ display: flex; gap: 20px; flex-wrap: wrap; }}
                    .stat {{ flex: 1; min-width: 120px; }}
                    .stat-value {{ font-size: 32px; font-weight: bold; color: #0284c7; margin: 5px 0; }}
                    .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .change-item {{ background: #fafafa; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 4px; font-size: 14px; }}
                    .button {{ display: inline-block; padding: 14px 28px; background: #667eea; color: white !important; text-decoration: none; border-radius: 6px; margin: 25px 0; font-weight: 600; transition: background 0.3s; }}
                    .button:hover {{ background: #5568d3; }}
                    .footer {{ background: #fafafa; padding: 25px 30px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
                    .footer a {{ color: #667eea; text-decoration: none; }}
                    .footer a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔔 Azure Service Tags Updated</h1>
                        <p>Weekly change summary from your subscription</p>
                    </div>
                    <div class="content">
                        <div class="summary">
                            <h2>📊 Change Summary</h2>
                            <div class="summary-stats">
                                <div class="stat">
                                    <div class="stat-value">{total_changes}</div>
                                    <div class="stat-label">Services Changed</div>
                                </div>
                            </div>
                            <p style="margin-top: 15px; font-size: 13px; color: #64748b;">
                                <strong>Detected:</strong> {timestamp}
                            </p>
                        </div>
                        
                        <h3 style="margin-top: 30px; font-size: 16px; color: #1e293b;">Recent Changes:</h3>
                        {changes_html}
                        
                        <div style="text-align: center;">
                            <a href="{self.app_url}/history.html" class="button">📈 View Full Change History</a>
                        </div>
                        
                        <div style="margin-top: 30px; padding: 20px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px; font-size: 13px;">
                            <strong>💡 What's Next?</strong><br>
                            Review these changes to update your firewall rules, network security groups, or service endpoints accordingly.
                        </div>
                    </div>
                    <div class="footer">
                        <p style="margin: 0 0 10px 0;">You're receiving this because you subscribed to Azure Service Tags updates.</p>
                        <p style="margin: 0;"><a href="{self.app_url}/unsubscribe.html">Manage Subscription</a> | <a href="{self.app_url}">Dashboard</a></p>
                        <p style="margin: 15px 0 0 0; color: #9ca3af;">Azure Service Tags Tracker<br>Automated monitoring powered by GitHub Actions</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send to all recipients
            success_count = 0
            for email in recipients:
                try:
                    message = Mail(
                        from_email=Email(self.from_email, self.from_name),
                        to_emails=To(email),
                        subject=f'🔔 Azure Service Tags Updated - {total_changes} Services Changed',
                        html_content=Content("text/html", html_content)
                    )
                    
                    response = self.client.send(message)
                    if response.status_code in [200, 202]:
                        success_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to send to {email}: {e}")
            
            print(f"✅ Change notifications sent to {success_count}/{len(recipients)} subscribers")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Error sending notifications: {e}")
            import traceback
            traceback.print_exc()
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
