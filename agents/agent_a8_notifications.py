"""
Agent A8 - Notifications (Minimalist - With Approve/Reject Buttons)
Primary Function: send_notifications()
Purpose: Sends emails with clickable buttons
"""
from typing import Dict, Any
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

USE_REAL_SMTP = True
SMTP_CONFIG = {
    'host': 'hosted-ex01.go4hosting.in',
    'port': 587,
    'username': 'omfys.test@omfysgroup.com',
    'password': 'Omfys@123',
    'from_email': 'omfys.test@omfysgroup.com',
    'from_name': 'Leave Management System'
}
BASE_URL = "http://localhost:8501"


def send_notifications(state: Dict[str, Any]) -> Dict[str, Any]:
    """PRIMARY FUNCTION - LangGraph Entry Point"""
    approve_token = state.get('approval_workflow', {}).get('approve_token')
    deny_token = state.get('approval_workflow', {}).get('deny_token')
    
    if not approve_token or not deny_token:
        result = {"admin_email_sent": False, "employee_notification_sent": False, "error": "No tokens"}
        _log_state("A8 - Notifications (ERROR)", state, result)
        return result
    
    approve_url = f"{BASE_URL}/approve/{approve_token}"
    reject_url = f"{BASE_URL}/reject/{deny_token}"
    
    admin_result = _send_admin_email(state, approve_url, reject_url)
    employee_result = _send_employee_email(state)
    
    result = {
        "admin_email_sent": admin_result['success'],
        "employee_notification_sent": employee_result['success'],
        "approve_url": approve_url,
        "reject_url": reject_url
    }
    
    _log_state("A8 - Notifications", state, result)
    return result


def _send_admin_email(state, approve_url, reject_url):
    """Send admin email with buttons"""
    kt_section = ""
    if state.get('kt_details', {}).get('validation_status') == 'complete':
        kt = state['kt_details']
        kt_section = f"""
        <div style="background:#f5f5f5;padding:15px;margin:20px 0;border-left:4px solid #2196F3">
            <h3 style="margin-top:0;color:#1976D2">📋 Knowledge Transfer</h3>
            <p><strong>Handover To:</strong> {kt.get('handover_to', 'N/A')}<br>
            <strong>Summary:</strong> {kt.get('summary', 'N/A')[:200]}<br>
            <strong>Document:</strong> {'✅ Uploaded' if kt.get('document_uploaded') else '❌ None'}</p>
        </div>"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:8px 8px 0 0;text-align:center">
            <h1 style="margin:0">🔔 Leave Approval Required</h1>
        </div>
        <div style="background:white;padding:30px;border:1px solid #e0e0e0">
            <p>Hello <strong>{state.get('admin_name', 'Admin')}</strong>,</p>
            <p>A leave request requires your approval.</p>
            <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0">
            
            <div style="background:#f9f9f9;padding:15px;border-radius:8px;margin:20px 0">
                <h3 style="margin-top:0">👤 Employee</h3>
                <p><strong>Name:</strong> {state['employee_name']} ({state['employee_code']})<br>
                <strong>Department:</strong> {state['employee_department']}<br>
                <strong>Designation:</strong> {state['employee_designation']}</p>
            </div>
            
            <div style="background:#fff3e0;padding:15px;border-radius:8px;margin:20px 0">
                <h3 style="margin-top:0;color:#e65100">📅 Leave Details</h3>
                <p><strong>Type:</strong> {state['leave_type']}<br>
                <strong>Duration:</strong> <strong style="color:#e65100">{state['working_days']} days</strong><br>
                <strong>Start:</strong> {state['leave_start_date']}<br>
                <strong>End:</strong> {state['leave_end_date']}<br>
                <strong>Reason:</strong> {state['leave_reason']}</p>
            </div>
            
            {kt_section}
            
            <hr style="border:none;border-top:2px solid #e0e0e0;margin:30px 0">
            
            <div style="text-align:center;margin:30px 0">
                <h2 style="color:#333;margin-bottom:20px">⚡ Take Action</h2>
                <a href="{approve_url}" style="display:inline-block;background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);color:white;padding:15px 40px;text-decoration:none;border-radius:8px;font-weight:bold;margin:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)">✅ APPROVE</a>
                <br>
                <a href="{reject_url}" style="display:inline-block;background:linear-gradient(135deg,#eb3349 0%,#f45c43 100%);color:white;padding:15px 40px;text-decoration:none;border-radius:8px;font-weight:bold;margin:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)">❌ REJECT</a>
            </div>
            
            <div style="background:#fff9e6;padding:15px;border-radius:8px;border-left:4px solid #ffc107">
                <p style="margin:0;font-size:13px;color:#666"><strong>⏰ Expires in 48 hours</strong></p>
            </div>
            
            <p style="margin-top:30px;font-size:13px;color:#999;text-align:center">
                Leave Management System<br>Thread: {state.get('thread_id', 'N/A')}
            </p>
        </div>
    </body>
    </html>"""
    
    subject = f"🔔 Approval Required: {state['employee_name']} - {state['working_days']} days"
    return _send_email(state.get('admin_email'), subject, html, True)


def _send_employee_email(state):
    """Send employee confirmation"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:8px;text-align:center">
            <h2 style="margin:0">✅ Request Submitted</h2>
        </div>
        <div style="padding:30px;border:1px solid #e0e0e0">
            <p>Hello <strong>{state['employee_name']}</strong>,</p>
            <p>Your leave request has been submitted for approval.</p>
            <div style="background:#e3f2fd;padding:15px;border-radius:8px;margin:20px 0">
                <h3 style="margin-top:0;color:#1976D2">📋 Summary</h3>
                <p><strong>Type:</strong> {state['leave_type']}<br>
                <strong>Start:</strong> {state['leave_start_date']}<br>
                <strong>End:</strong> {state['leave_end_date']}<br>
                <strong>Duration:</strong> {state['working_days']} days<br>
                <strong>Status:</strong> <span style="color:#ff9800">⏳ Pending</span></p>
            </div>
            <p>Manager <strong>{state.get('admin_name', 'Manager')}</strong> has been notified.</p>
            <p style="margin-top:30px;font-size:13px;color:#999;text-align:center">Leave Management System</p>
        </div>
    </body>
    </html>"""
    
    subject = f"Leave Request Submitted - {state['working_days']} days"
    return _send_email(state.get('employee_email'), subject, html, True)


def _send_email(to_email, subject, body, is_html=False):
    """Send email via SMTP"""
    try:
        if USE_REAL_SMTP:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{SMTP_CONFIG['from_name']} <{SMTP_CONFIG['from_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'])
            server.starttls()
            server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            return {'success': True, 'message': 'Email sent'}
        return {'success': True, 'message': '[MOCK] Email sent'}
    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}


def _log_state(agent_name: str, state: Dict[str, Any], output: Dict[str, Any]):
    """Log complete state"""
    print("\n" + "="*80)
    print(f"🤖 AGENT: {agent_name}")
    print("="*80)
    print("\n📥 INPUT STATE:")
    print("-"*80)
    print(json.dumps(state, indent=2, default=str))
    print("\n📤 OUTPUT/UPDATES:")
    print("-"*80)
    print(json.dumps(output, indent=2, default=str))
    print("\n" + "="*80 + "\n")
