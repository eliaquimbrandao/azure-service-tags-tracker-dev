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
        self.app_url = os.getenv('APP_URL', 'https://eliaquimbrandao.github.io/azure-service-tags-tracker-dev')
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
    
    def send_change_notification(self, recipients: List[Dict], changes: Dict) -> bool:
        """
        Send notification email about Azure Service Tags changes.

        Recipients carry context so the email can explain why they got it
        (all services vs filtered selection) and show a scoped summary when
        applicable.

        Args:
            recipients: List of dicts with keys email, subscriptionType, selectedServices
            changes: Change data from latest-changes.json

        Returns:
            True if at least one email was sent successfully
        """
        if not self.client:
            print(f"⚠️ SendGrid not configured. Would send to {len(recipients)} recipients")
            return False
        
        try:
            # Summarize change payload for a compact snapshot
            change_list = changes.get('changes', [])
            services_changed = len(change_list)
            # Dates: Microsoft publish vs our detection vs change week
            timestamp = changes.get('generated_at') or changes.get('timestamp') or 'Not provided'
            published_date = (changes.get('metadata') or {}).get('date_published') or changes.get('date') or timestamp
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

            # Prefer regional count from summary when available (matches dashboard)
            regional_map = changes.get('regional_changes') if isinstance(changes.get('regional_changes'), dict) else None
            regions_from_summary = len([r for r, count in regional_map.items() if count]) if regional_map else regions_changed

            def _fmt_date(value) -> str:
                """Return date-only label (YYYY-MM-DD) for ISO/timestamp strings."""
                if not value:
                    return "Not provided"
                if isinstance(value, datetime):
                    return value.date().isoformat()
                if isinstance(value, str):
                    cleaned = value.strip()
                    # Try ISO parsing first (handles timezone offsets and Z)
                    try:
                        iso_candidate = cleaned.replace('Z', '+00:00')
                        return datetime.fromisoformat(iso_candidate).date().isoformat()
                    except Exception:
                        pass
                    formats = [
                        "%Y-%m-%d",
                        "%m/%d/%Y",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f%z",
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%S%z",
                    ]
                    for fmt in formats:
                        try:
                            return datetime.strptime(cleaned[:len(fmt.replace('%z',''))], fmt).date().isoformat()
                        except ValueError:
                            continue
                    if len(cleaned) >= 10:
                        return cleaned[:10]
                    return cleaned
                return str(value)

            def send_upgrade_magic_link(self, email: str, link: str) -> bool:
                """Send a short-lived magic link so the user can finalize premium and set a password."""
                if not email:
                    return False
                if not link:
                    return False

                subject = "Complete your premium upgrade"
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background: #f7f7fb; color: #1f2937; }}
                        .container {{ max-width: 560px; margin: 0 auto; padding: 24px; }}
                        .card {{ background: #ffffff; border-radius: 10px; padding: 24px; box-shadow: 0 10px 35px rgba(31,41,55,0.08); }}
                        .btn {{ display: inline-block; background: #2563eb; color: #fff; padding: 12px 18px; border-radius: 8px; text-decoration: none; font-weight: 600; }}
                        .muted {{ color: #6b7280; font-size: 14px; margin-top: 12px; }}
                        .code {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; background: #f3f4f6; padding: 4px 8px; border-radius: 6px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="card">
                            <h2>Finish upgrading to Premium</h2>
                            <p>Click the button below to confirm your email and create a password. This link expires soon for security.</p>
                            <p><a class="btn" href="{link}" target="_blank" rel="noopener">Complete upgrade</a></p>
                            <p class="muted">If the button does not work, copy and paste this link into your browser:</p>
                            <p class="code">{link}</p>
                            <p class="muted">You are receiving this because someone requested a premium upgrade for this email.</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                if not self.client:
                    print("⚠️ SendGrid not configured. Upgrade link for", email, "=>", link)
                    return False

                try:
                    message = Mail(
                        from_email=Email(self.from_email, self.from_name),
                        to_emails=To(email),
                        subject=subject,
                        html_content=Content("text/html", html_content)
                    )
                    response = self.client.send(message)
                    return response.status_code in [200, 202]
                except Exception as e:
                    print(f"❌ Error sending upgrade magic link: {e}")
                    return False

            detected_label = _fmt_date(timestamp)
            published_label = _fmt_date(published_date)

            def scoped_stats(selected_services: List[str]):
                if not selected_services:
                    # All-services subscription: use summary region count if present
                    return services_changed, regions_from_summary, added_total, removed_total
                svc_changed = 0
                svc_regions = set()
                svc_added = 0
                svc_removed = 0
                for item in change_list:
                    if item.get('service') not in selected_services:
                        continue
                    svc_changed += 1
                    svc_added += item.get('added_count', len(item.get('added_prefixes', [])))
                    svc_removed += item.get('removed_count', len(item.get('removed_prefixes', [])))
                    region = item.get('region')
                    if region:
                        svc_regions.add(region)
                return svc_changed, len(svc_regions), svc_added, svc_removed

            success_count = 0
            for recipient in recipients:
                email = recipient['email']
                subscription_type = recipient.get('subscriptionType', 'all')
                selected_services = recipient.get('selectedServices', []) or []

                scoped_services_changed, scoped_regions, scoped_added, scoped_removed = scoped_stats(selected_services)

                reason = "You receive this because you subscribed to all Azure Service Tags changes."
                if subscription_type == 'filtered':
                    reason = "You receive this because you subscribed to updates for specific services." + \
                             (" Services: " + ", ".join(selected_services) if selected_services else "")

                # Plaintext part (keeps size tiny and forwards cleanly)
                text_lines = [
                    "Azure Service Tags update",
                    reason,
                    "We detected new Azure Service Tags activity this week. Review the dashboard for a complete list of every service and IP range that changed, plus historical context and filtering tools.",
                    f"Services changed: {scoped_services_changed}",
                    f"Regions touched: {scoped_regions}",
                    f"IPs added: {scoped_added} | removed: {scoped_removed}",
                    f"Published by Microsoft: {published_label}",
                    f"Detected by tracker: {detected_label}",
                    f"Details: {self.app_url}/history.html",
                    f"Manage subscription: {self.app_url}/unsubscribe.html",
                ]
                text_body = "\n".join(text_lines)

                # Compact HTML summary mirroring the dashboard hero stats with a dark header
                subscription_line = "Weekly change summary from your subscription to all Azure Service Tags & IP ranges changes." if subscription_type == 'all' else "Weekly change summary for your subscription to selected Azure Service Tags changes."

                html_content = f"""
                                <!DOCTYPE html>
                                <html>
                                    <head>
                                        <meta charset=\"UTF-8\">
                                        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
                                        <style>
                                            body {{ margin:0; padding:0; background:#f7f9fb; font-family: Arial, sans-serif; color:#1f2937; }}
                                            .card {{ max-width:620px; margin:12px auto; background:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 4px 14px rgba(0,0,0,0.08); }}
                                            .header {{ background:#0f172a; color:#e2e8f0; padding:16px 20px 14px 20px; }}
                                            .header h1 {{ margin:0; font-size:18px; font-weight:700; color:#e0f2fe; }}
                                            .header p {{ margin:6px 0 0 0; font-size:13px; color:#cbd5e1; }}
                                            .body {{ padding:18px 20px 20px 20px; }}
                                              .pill {{ display:inline-block; padding:6px 10px; border-radius:999px; background:#e0f2fe; color:#0f172a; font-size:11px; margin-bottom:8px; font-weight:600; }}
                                              .pill.secondary {{ background:#eef2ff; color:#312e81; margin-left:6px; }}
                                              .pill.tertiary {{ background:#e8f5e9; color:#0f5132; margin-left:6px; }}
                                            .reason {{ margin:0 0 12px 0; color:#334155; font-size:13px; }}
                                              .stats-table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
                                              .stats-table td {{ width:25%; background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; text-align:center; padding:12px; font-family: Arial, sans-serif; }}
                                              .stat h3 {{ margin:0; font-size:22px; color:#0f172a; }}
                                              .stat p {{ margin:4px 0 0 0; font-size:12px; color:#475569; }}
                                                                                            .cta {{ display:inline-block; padding:11px 16px; color:#ffffff !important; font-weight:650; font-size:13px; text-decoration:none; font-family: Arial, sans-serif; }}
                                                                                            .cta:hover {{ background:#1e40af; color:#ffffff !important; }}
                                            .footer {{ margin-top:16px; font-size:12px; color:#6b7280; }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class=\"card\">
                                            <div class=\"header\">
                                                <h1>Azure Service Tags update</h1>
                                                <p>{subscription_line}</p>
                                            </div>
                                            <div class=\"body\">
                                                    <div class=\"pill secondary\">Published by Microsoft: {published_label}</div><div class=\"pill tertiary\">Detected by tracker: {detected_label}</div>
                                                <p class=\"reason\">{reason}</p>
                                                <p class=\"reason\">We detected new Azure Service Tags activity this week. Review the dashboard for a complete list of every service and IP range that changed, plus historical context and filtering tools.</p>
                                                                                                <table class=\"stats-table\" role=\"presentation\">
                                                                                                    <tr>
                                                                                                        <td class=\"stat\"><h3>{scoped_services_changed}</h3><p>services changed</p></td>
                                                                                                        <td class=\"stat\"><h3>{scoped_regions}</h3><p>regions touched</p></td>
                                                                                                        <td class=\"stat\"><h3>{scoped_added}</h3><p>IPs added</p></td>
                                                                                                        <td class=\"stat\"><h3>{scoped_removed}</h3><p>IPs removed</p></td>
                                                                                                    </tr>
                                                                                                </table>
                                                                                                <table role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\" border=\"0\" style=\"margin-top:12px;\">
                                                                                                    <tr>
                                                                                                        <td class=\"cta\" align=\"center\" bgcolor=\"#1d4ed8\" style=\"border-radius:8px;\">
                                                                                                            <a href=\"{self.app_url}/history.html\" style=\"display:inline-block; padding:11px 16px; color:#ffffff !important; font-weight:650; font-size:13px; text-decoration:none; font-family: Arial, sans-serif;\">View detailed changes</a>
                                                                                                        </td>
                                                                                                    </tr>
                                                                                                </table>
                                                <div class=\"footer\">Manage subscription: <a href=\"{self.app_url}/unsubscribe.html\" style=\"color:#1d4ed8; text-decoration:none;\">unsubscribe</a> · Dashboard: <a href=\"{self.app_url}\" style=\"color:#1d4ed8; text-decoration:none;\">open</a></div>
                                            </div>
                                        </div>
                                    </body>
                                </html>
                                """

                try:
                    message = Mail(
                        from_email=Email(self.from_email, self.from_name),
                        to_emails=To(email),
                        subject='Weekly Update: Azure Public Cloud IP Ranges & Service Tags changes',
                        html_content=Content("text/html", html_content)
                    )

                    # Add plaintext alternative to improve deliverability/forwarding
                    message.add_content(Content("text/plain", text_body))

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
