import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str):
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            logging.warning("SENDGRID_API_KEY not set. Mocking email sending.")
            logging.info(f"Mock Email sent to {to_email} with subject: {subject}")
            return False
            
        message = Mail(
            from_email='noreply@eventra.com', # Must be verified in SendGrid
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        try:
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            logging.info(f"Email sent to {to_email}. Status Code: {response.status_code}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False

    @staticmethod
    def send_registration_confirmation(to_email: str, student_name: str, event_title: str, ticket_number: str):
        subject = f"Registration Confirmed: {event_title}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Registration Successful!</h2>
            <p>Hi {student_name},</p>
            <p>You have successfully registered for <strong>{event_title}</strong>.</p>
            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #6b7280; font-size: 12px; text-transform: uppercase;">Your Ticket Number</p>
                <p style="margin: 10px 0 0 0; font-size: 24px; font-weight: bold; color: #111827;">{ticket_number}</p>
            </div>
            <p>Please show this ticket number or the QR code in your dashboard at the event venue.</p>
            <p>See you there!</p>
            <p>Best,<br>Eventra Team</p>
        </div>
        """
        return EmailService.send_email(to_email, subject, html_content)
