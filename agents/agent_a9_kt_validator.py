"""
Agent A9 - KT Validator
Primary Function: validate_knowledge_transfer()
Purpose: Validates and collects KT for leaves > 3 days
"""
from typing import Dict, Any, Optional
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'leave_system.db')


def validate_knowledge_transfer(state: Dict[str, Any], user_input: Optional[str] = None, uploaded_file=None) -> Dict[str, Any]:
    """PRIMARY FUNCTION - LangGraph Entry Point"""
    working_days = state.get('working_days', 0)
    
    if working_days <= 3:
        result = {
            "kt_details": {
                "required": False,
                "validation_status": "complete",
                "handover_to": None,
                "summary": None,
                "document_uploaded": False
            },
            "awaiting_kt_input": False
        }
        _log_state("A9 - KT Validator (Skipped)", state, result)
        return result
    
    kt_step = state.get('kt_step', 1)
    
    if kt_step == 1:
        result = _collect_handover_employee(state, user_input)
    elif kt_step == 2:
        result = _collect_summary(state, user_input)
    elif kt_step == 3:
        result = _collect_document(state, user_input, uploaded_file)
    else:
        result = {
            "kt_details": {"required": True, "validation_status": "in_progress"},
            "awaiting_kt_input": True
        }
    
    # ===== LOG STATE =====
    _log_state(f"A9 - KT Validator (Step {kt_step})", state, result)
    
    return result


def _log_state(agent_name: str, state: Dict[str, Any], output: Dict[str, Any]):
    """Log complete state"""
    print("\n" + "="*80)
    print(f"🤖 AGENT: {agent_name}")
    print("="*80)
    print("\n📥 INPUT STATE:")
    print("-"*80)
    import json
    print(json.dumps(state, indent=2, default=str))
    print("\n📤 OUTPUT/UPDATES:")
    print("-"*80)
    print(json.dumps(output, indent=2, default=str))
    print("\n" + "="*80 + "\n")


def search_employee(query: str) -> list:
    """Search employee in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emp_id, emp_code, name, department, designation
        FROM EMPLOYEE WHERE name LIKE ? OR emp_code LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    conn.close()
    return [{'emp_id': r[0], 'emp_code': r[1], 'name': r[2], 'department': r[3], 'designation': r[4]} for r in results]


def collect_kt_details(emp_id: int, handover_to_emp_id: int, summary: str, file_name: Optional[str] = None) -> Dict[str, Any]:
    """Save KT to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    doc_code = f"KT-2026-{timestamp}"
    cursor.execute("""
        INSERT INTO KT_DOCUMENTS (document_code, emp_id, handover_to_emp_id, handover_summary, file_name, file_path, upload_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (doc_code, emp_id, handover_to_emp_id, summary, file_name, f"/kt-docs/{doc_code}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {'document_code': doc_code, 'saved': True}


def _collect_handover_employee(state: Dict[str, Any], user_input: Optional[str]) -> Dict[str, Any]:
    """Step 1"""
    if not user_input:
        return {
            "kt_details": {"required": True, "validation_status": "in_progress"},
            "awaiting_kt_input": True,
            "kt_step": 1,
            "kt_message": "Who will handle your work?"
        }
    
    employees = search_employee(user_input)
    if len(employees) == 1:
        return {
            "kt_details": {"required": True, "validation_status": "in_progress", "handover_to": employees[0]['name']},
            "awaiting_kt_input": True,
            "kt_step": 2,
            "kt_handover_emp": employees[0],
            "kt_message": f"Found: {employees[0]['name']}. Provide handover summary (min 50 chars):"
        }
    return {
        "kt_details": {"required": True, "validation_status": "in_progress"},
        "awaiting_kt_input": True,
        "kt_step": 1,
        "kt_message": f"Found {len(employees)} employees. Enter employee code:"
    }


def _collect_summary(state: Dict[str, Any], user_input: Optional[str]) -> Dict[str, Any]:
    """Step 2"""
    if not user_input or len(user_input) < 50:
        return {
            "kt_details": {"required": True, "validation_status": "in_progress"},
            "awaiting_kt_input": True,
            "kt_step": 2,
            "kt_message": "Summary too short (min 50 chars)."
        }
    return {
        "kt_details": {"required": True, "validation_status": "in_progress", "summary": user_input},
        "awaiting_kt_input": True,
        "kt_step": 3,
        "kt_summary": user_input,
        "kt_message": "Upload document (optional) or type 'skip':"
    }


def _collect_document(state: Dict[str, Any], user_input: Optional[str], uploaded_file) -> Dict[str, Any]:
    """Step 3"""
    handover_emp = state.get('kt_handover_emp', {})
    summary = state.get('kt_summary', '')
    file_name = uploaded_file.name if uploaded_file else None
    
    result = collect_kt_details(
        emp_id=state['employee_id'],
        handover_to_emp_id=handover_emp.get('emp_id'),
        summary=summary,
        file_name=file_name
    )
    
    return {
        "kt_details": {
            "required": True,
            "validation_status": "complete",
            "handover_to": handover_emp.get('name'),
            "summary": summary,
            "document_uploaded": file_name is not None
        },
        "awaiting_kt_input": False,
        "kt_document_code": result['document_code']
    }
