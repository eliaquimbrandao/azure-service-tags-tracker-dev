"""
Email Service using SendGrid
Handles sending confirmation and notification emails.
"""

import os
from datetime import datetime
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
            # Summarize change payload for the email snapshot
            change_list = changes.get('changes', [])
            services_changed = len(change_list)
            timestamp = changes.get('timestamp', 'Unknown')
            published_date = changes.get('date') or timestamp
            regions_changed = 0
            added_total = 0
            removed_total = 0
            seen_regions = set()

            for item in change_list:
                added_total += item.get('added_count', len(item.get('added_prefixes', [])))
                removed_total += item.get('removed_count', len(item.get('removed_prefixes', [])))
                region = item.get('region')
                if region:
                    seen_regions.add(region)

            if seen_regions:
                regions_changed = len(seen_regions)

            formatted_date = published_date
            if published_date and isinstance(published_date, str):
                try:
                    parsed = datetime.strptime(published_date[:10], "%Y-%m-%d")
                    formatted_date = parsed.strftime("%A, %B %d, %Y")
                except ValueError:
                    formatted_date = published_date

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
                    .summary {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 24px; margin: 24px 0; border-radius: 8px; }}
                    .summary h2 {{ margin: 0 0 10px 0; font-size: 18px; color: #0c4a6e; }}
                    .summary p {{ margin: 5px 0; color: #0f172a; font-size: 14px; }}
                    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; margin-top: 20px; }}
                    .stat-card {{ background: white; border-radius: 6px; padding: 16px; border: 1px solid #e2e8f0; text-align: center; }}
                    .stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .stat-value {{ font-size: 28px; font-weight: 600; color: #0284c7; margin-top: 6px; }}
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
                            <p><strong>{formatted_date}</strong></p>
                            <p style="color:#475569;">Detected: {timestamp}</p>
                            <div class="summary-grid">
                                <div class="stat-card">
                                    <div class="stat-label">Services</div>
                                    <div class="stat-value">{services_changed}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Regions</div>
                                    <div class="stat-value">{regions_changed}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Added IPs</div>
                                    <div class="stat-value" style="color:#16a34a;">{added_total}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Removed IPs</div>
                                    <div class="stat-value" style="color:#dc2626;">{removed_total}</div>
                                </div>
                            </div>
                        </div>
                        <p style="font-size:15px; color:#1f2937; line-height:1.8;">
                            We detected new Azure Service Tags activity this week. Review the dashboard for a complete list of every service and IP range that changed, plus historical context and filtering tools.
                        </p>
                        <div style="text-align: center;">
                            <a href="{self.app_url}/history.html" class="button">📈 View Detailed Changes</a>
                        </div>
                        <p style="font-size:13px; color:#475569; background:#eef2ff; border-left:4px solid #4338ca; padding:16px; border-radius:6px;">
                            Tip: Bookmark the dashboard or share it with your network team so they can evaluate firewall rules, NSGs, and service endpoints whenever Microsoft publishes new IP ranges.
                        </p>
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
                        subject=f'🔔 Azure Service Tags Updated - {services_changed} Services Changed',
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
    
    def send_unsubscribe_verification(self, email: str, verification_token: str) -> bool:
        """
        Send verification email for unsubscribe request
        
        Args:
            email: User's email address
            verification_token: Temporary verification token
        
        Returns:
            True if sent successfully
        """
        if not self.client:
            print("⚠️ SendGrid not configured. Verification email would be sent to:", email)
            self._log_verification_email_to_console(email, verification_token)
            return False
        
        try:
            verification_url = f"{self.app_url}/unsubscribe.html?email={email}&verify={verification_token}"
            
            # Prepare email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; padding: 14px 28px; background: #ef4444; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                    .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ Confirm Unsubscribe Request</h1>
                    </div>
                    <div class="content">
                        <p>We received a request to unsubscribe <strong>{email}</strong> from Azure Service Tags update notifications.</p>
                        
                        <div class="warning">
                            <strong>⏰ This link expires in 15 minutes</strong><br>
                            For your security, this verification link will expire shortly.
                        </div>
                        
                        <p><strong>If this was you:</strong></p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">✅ Confirm Unsubscribe</a>
                        </p>
                        
                        <p><strong>If this wasn't you:</strong></p>
                        <p>Simply ignore this email. Your subscription will remain active and no changes will be made.</p>
                        
                        <div class="footer">
                            <p><strong>Why did I receive this?</strong><br>
                            Someone (hopefully you) requested to unsubscribe this email address from our service. 
                            We require email verification to prevent unauthorized unsubscribe requests.</p>
                            
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
                to_emails=To(email),
                subject='⚠️ Confirm Your Unsubscribe Request',
                html_content=Content("text/html", html_content)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Verification email sent to {email}")
                return True
            else:
                print(f"⚠️ Email send failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending verification email: {e}")
            return False
    
    def _log_verification_email_to_console(self, email: str, verification_token: str):
        """Log verification email content to console for development"""
        verification_url = f"{self.app_url}/unsubscribe.html?email={email}&verify={verification_token}"
        
        print("\n" + "="*60)
        print("📧 UNSUBSCRIBE VERIFICATION EMAIL (Development Mode)")
        print("="*60)
        print(f"To: {email}")
        print(f"Subject: ⚠️ Confirm Your Unsubscribe Request")
        print(f"\nClick to confirm unsubscribe:")
        print(f"{verification_url}")
        print(f"\n⏰ Link expires in 15 minutes")
        print("="*60 + "\n")
    
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
