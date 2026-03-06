"""
Agent A7 - Transaction Executor (Minimalist - API Integrated)
Calls real API to create leave, no external files needed
"""
from typing import Dict, Any
import json
import requests

API_BASE_URL = "https://devmcdphcmplatform.omfysgroup.com"
AUTH_URL = "https://dev_mcdp_be.omfysgroup.com/auth/token"


def _log_state(agent_name: str, state: Dict[str, Any], output: Dict[str, Any]):
    """Log complete state - MUST BE DEFINED FIRST"""
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


def execute_transaction(state: Dict[str, Any]) -> Dict[str, Any]:
    """PRIMARY FUNCTION - Calls real API to create leave"""
    try:
        # Get auth token
        token = _get_auth_token()
        if not token:
            raise Exception("Failed to get authentication token")
        
        # Prepare API payload
        kt_details = state.get('kt_details', {})
        
        payload = {
            'dayType': 'Full Day',
            'leaveType': _map_leave_type(state.get('leave_type', 'PL')),
            'ktStatus': 'Yes' if kt_details.get('required') else 'No',
            'handOverEmployee': str(kt_details.get('handover_emp_id', '')),
            'knowledgeSummary': kt_details.get('summary', ''),
            'purpose': state.get('leave_reason', ''),
            'reason': 2,
            'startDate': state.get('leave_start_date'),
            'endDate': state.get('leave_end_date'),
            'notificationdate': state.get('leave_start_date'),
            'reportingmanagerstatus': 'Yes',
            'attachement': kt_details.get('document_base64', ''),
            'file': ''
        }
        
        print(f"\n📤 Calling API: POST /user/leaves/applyLeave")
        print(f"Payload: {json.dumps({**payload, 'attachement': '...' if payload['attachement'] else ''}, indent=2)}")
        
        # Call API
        response = requests.post(
            f"{API_BASE_URL}/user/leaves/applyLeave",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            json=payload
        )
        response.raise_for_status()
        
        api_result = response.json()
        
        # Extract Leave Request ID
        leave_request_id = (
            api_result.get('leaveRequestId') or 
            api_result.get('requestId') or 
            api_result.get('id') or
            api_result.get('data', {}).get('id')
        )
        
        if not leave_request_id:
            raise Exception("API did not return Leave Request ID")
        
        leave_request_id = str(leave_request_id)
        
        # FINAL STATE
        result = {
            "transaction_result": {
                "success": True,
                "leave_request_id": leave_request_id,
                "api_response": api_result
            },
            "Leave_Request_ID": leave_request_id,
            "Transaction_Complete": "Yes",
            "Employee_email": "Yes",
            "workflow_completed": True,
            "status": "end",
            "chat_response": f"🎉 Your Leave has been Successfully Applied!! Request ID: {leave_request_id}"
        }
        
        _log_state("A7 - Transaction Executor (SUCCESS)", state, result)
        return result
        
    except Exception as e:
        result = {
            "transaction_result": {
                "success": False,
                "leave_request_id": None
            },
            "Leave_Request_ID": None,
            "Transaction_Complete": "No",
            "workflow_completed": False,
            "status": "error",
            "error": str(e),
            "chat_response": f"❌ Transaction failed: {str(e)}"
        }
        
        _log_state("A7 - Transaction Executor (ERROR)", state, result)
        return result


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


def _map_leave_type(leave_type: str) -> str:
    """Map leave type to API ID"""
    mapping = {
        'PL': '5',
        'SL': '6',
        'CL': '7'
    }
    return mapping.get(leave_type, '5')


def handle_cancellation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cancellation"""
    return {
        "cancelled": True,
        "status": "end",
        "chat_response": "❌ Leave request cancelled."
    }
