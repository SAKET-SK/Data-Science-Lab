"""
Agent A6 - Approval Setup (Minimalist - All Features Included)
No external dependencies, all API calls included here
"""
from typing import Dict, Any, Literal
import secrets
import redis
import json
import requests
from datetime import timedelta, datetime

REDIS_CONFIG = {'host': 'localhost', 'port': 6379, 'db': 0, 'decode_responses': True}
TOKEN_EXPIRY_HOURS = 48
TOKEN_PREFIX = 'leave_approval:'

# API Configuration
API_BASE_URL = "https://devmcdphcmplatform.omfysgroup.com"
AUTH_URL = "https://dev_mcdp_be.omfysgroup.com/auth/token"


def setup_approval_workflow(state: Dict[str, Any]) -> Dict[str, Any]:
    """PRIMARY FUNCTION - LangGraph Entry Point"""
    try:
        tokens = generate_approval_tokens()
        approve_token = tokens['approve_token']
        deny_token = tokens['deny_token']
        approval_id = f"APR-{approve_token[:8].upper()}"
        
        redis_client = _get_redis_client()
        
        if redis_client:
            leave_data = {
                'employee_id': state['employee_id'],
                'employee_name': state['employee_name'],
                'employee_email': state.get('employee_email'),
                'employee_code': state.get('employee_code'),
                'employee_department': state.get('employee_department'),
                'employee_designation': state.get('employee_designation'),
                'leave_start_date': state['leave_start_date'],
                'leave_end_date': state['leave_end_date'],
                'working_days': state['working_days'],
                'leave_type': state['leave_type'],
                'leave_reason': state['leave_reason'],
                'admin_id': state['admin_id'],
                'admin_name': state.get('admin_name'),
                'admin_email': state.get('admin_email'),
                'approval_status': 'pending',
                'created_at': datetime.now().isoformat(),
                'kt_required': state['working_days'] > 3,
                'thread_id': state.get('thread_id'),
                'current_balance': state.get('current_balance', 0),
                'kt_details': state.get('kt_details', {}),
                'approval_id': approval_id
            }
            
            redis_client.setex(
                f"{TOKEN_PREFIX}approve:{approve_token}",
                timedelta(hours=TOKEN_EXPIRY_HOURS),
                json.dumps(leave_data)
            )
            
            redis_client.setex(
                f"{TOKEN_PREFIX}deny:{deny_token}",
                timedelta(hours=TOKEN_EXPIRY_HOURS),
                json.dumps(leave_data)
            )
            
            _update_employee_status(redis_client, state['employee_id'], 'applied', leave_data)
        
        result = {
            "approval_workflow": {
                "requires_approval": True,
                "approval_status": "pending",
                "approve_token": approve_token,
                "deny_token": deny_token,
                "token_expires_in": TOKEN_EXPIRY_HOURS,
                "approval_id": approval_id
            },
            "Approval_ID": approval_id,
            "chat_response": "✅ Approval tokens generated. Proceeding to notifications..."
        }
        
        _log_state("A6 - Approval Setup", state, result)
        return result
            
    except Exception as e:
        result = {
            "approval_workflow": {
                "requires_approval": True,
                "approval_status": "error",
                "error": str(e)
            },
            "chat_response": f"❌ Error setting up approval: {str(e)}"
        }
        _log_state("A6 - Approval Setup (ERROR)", state, result)
        return result


def handle_approval_click(token: str, action: Literal["approve", "reject"], admin_ip: str = None) -> Dict[str, Any]:
    """Handle admin clicking approve/reject button"""
    try:
        validation_result = validate_token(token, action, admin_ip)
        
        if not validation_result['valid']:
            return {
                'success': False,
                'message': validation_result['message'],
                'error_type': 'invalid_token',
                'AR_approve': 'No',
                'status': 'end',
                'chat_response': f"❌ {validation_result['message']}"
            }
        
        leave_data = validation_result['leave_data']
        approval_id = leave_data.get('approval_id', f"APR-{token[:8].upper()}")
        
        if action == 'approve':
            return {
                'success': True,
                'action': 'approve',
                'leave_data': leave_data,
                'thread_id': leave_data.get('thread_id'),
                'AR_approve': 'Yes',
                'Approval_ID': approval_id,
                'status': 'approved',
                'chat_response': '✅ Admin approved! Executing transaction...'
            }
        else:  # reject
            return {
                'success': True,
                'action': 'reject',
                'leave_data': leave_data,
                'thread_id': leave_data.get('thread_id'),
                'AR_approve': 'No',
                'Approval_ID': approval_id,
                'status': 'end',
                'Transaction_Complete': 'No',
                'Leave_Request_ID': None,
                'chat_response': '❌ Your leave request was rejected by your manager.'
            }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'error_type': 'exception',
            'AR_approve': 'No',
            'status': 'end',
            'chat_response': f'❌ Error processing approval: {str(e)}'
        }


def get_admin_email_from_api(emp_id: int, token: str = None) -> Dict[str, Any]:
    """Get admin email from workflow API"""
    try:
        if not token:
            token = _get_auth_token()
        
        response = requests.get(
            f"{API_BASE_URL}/admin/workflow/assignment/{emp_id}",
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'admin_email': data.get('approvermail') or data.get('approvermail'),
            # 'admin_id': data.get('reportingManagerId') or data.get('managerId'),
            'admin_name': data.get('approvername') or data.get('approvername')
        }
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def _get_auth_token(emp_code: str = "OMI-0008", password: str = "Omfys@123") -> str:
    """Get Bearer token"""
    try:
        response = requests.post(
            AUTH_URL,
            headers={'Content-Type': 'application/json'},
            json={"empCode": emp_code, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        return data.get('token') or data.get('access_token')
    except Exception as e:
        print(f"❌ Auth Error: {str(e)}")
        return None


def validate_token(token: str, action: str, admin_ip: str = None) -> Dict[str, Any]:
    """Validate and consume token"""
    redis_client = _get_redis_client()
    if not redis_client:
        return {"valid": False, "message": "Redis unavailable"}
    
    key = f"{TOKEN_PREFIX}{action}:{token}"
    data_json = redis_client.get(key)
    
    if not data_json:
        return {"valid": False, "message": "Token expired or invalid"}
    
    leave_data = json.loads(data_json)
    
    if leave_data.get('approval_status') != 'pending':
        return {"valid": False, "message": "Token already used"}
    
    new_status = 'approved' if action == 'approve' else 'rejected'
    leave_data['approval_status'] = new_status
    leave_data['approved_at'] = datetime.now().isoformat()
    leave_data['admin_ip'] = admin_ip
    
    _update_employee_status(redis_client, leave_data['employee_id'], new_status, leave_data)
    
    audit_key = f"leave_audit:{leave_data['employee_id']}:{token[:8]}"
    redis_client.setex(audit_key, timedelta(days=365), json.dumps(leave_data))
    
    redis_client.delete(key)
    opposite = 'deny' if action == 'approve' else 'approve'
    redis_client.delete(f"{TOKEN_PREFIX}{opposite}:{token}")
    
    return {"valid": True, "leave_data": leave_data, "message": f"Leave {new_status}"}


def generate_approval_tokens() -> Dict[str, str]:
    """Generate secure tokens"""
    return {
        'approve_token': secrets.token_urlsafe(32),
        'deny_token': secrets.token_urlsafe(32)
    }


def _get_redis_client():
    """Get Redis connection"""
    try:
        client = redis.Redis(**REDIS_CONFIG)
        client.ping()
        return client
    except:
        return None


def _update_employee_status(redis_client, employee_id: int, status: str, leave_data: Dict):
    """Update employee leave status in Redis"""
    status_key = f"employee_leave_status:{employee_id}"
    status_data = {
        'employee_id': employee_id,
        'status': status,
        'updated_at': datetime.now().isoformat(),
        'leave_details': leave_data
    }
    redis_client.setex(status_key, timedelta(days=90), json.dumps(status_data))


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
