# agent_a5_plan_optimizer_helper.py

"""
LANGGRAPH STATE ACCESSOR - ACTUAL AGENT OUTPUTS
Functions to read data from server's LangGraph state

Company Policy: Only CL, PL, and LWP are available (NO SL)
"""

from typing import Dict, Any


# ============================================
# AGENT 1: INTENT PARSER
# ============================================

def parse_intent_and_dates() -> Dict[str, Any]:
    """
    Reads Agent 1's data from LangGraph state
    
    Returns:
        Agent 1's stored output with leave dates and reason
    """
    
    # ACTUAL KEYS from your agent (values will be dynamic)
    return {
        "intent_type": "apply_leave",
        "start_date": "2026-01-26",
        "end_date": "2026-02-03",
        "reason": "Going Outstation",
        "calendar_days": 10,
        "medical_document": None,
        "awaiting_field": None,
        "preview_confirmed": True,
        "application_date": "2026-01-23",
        "parsing_status": "complete",
        "daytype": "fullday",  # Can be: "halfday_1st", "halfday_2nd", "fullday"
        "missing_fields": [],
        "chat_response": ""
    }


# ============================================
# AGENT 2: GENUINENESS ASSESSOR
# ============================================

def assess_genuineness() -> Dict[str, Any]:
    """
    Reads Agent 2's data from LangGraph state
    
    Returns:
        Agent 2's stored output
        
    CRITICAL: If recommendation != "approve", Agent 5 will NOT generate plans
    """
    
    return {
        "genuineness_assessment": {
            "total_score": 72.5,
            "recommendation": "approve"  # CRITICAL: "approve" or other
        },
        "workflow_completed": True,
        "status": "completed",
        "chat_response": "Request validated. Checking eligibility."
    }


# ============================================
# AGENT 3: POLICY CHECKER
# ============================================

def check_policy() -> Dict[str, Any]:
    """
    Reads Agent 3's data from LangGraph state
    
    Returns:
        Agent 3's stored output
        
    NOTE: This is used for reference, but Agent 4's eligibility is PRIMARY
    """
    
    return {
        "cl_allowed_for_family_function": False,
        "pl_allowed_for_family_function": False,
        "max_cl_consecutive_days": 0.0,
        "max_pl_consecutive_days": 0.0,
        "weekends_counted_for_leave": True,
        "minimum_team_availability_percentage": 60,
        "lwp_allowed": True,
        "lwp_allowed_for_trainee": True,
        "max_lwp_consecutive_days": 10
    }


# ============================================
# AGENT 4: ELIGIBILITY CHECKER (PRIMARY SOURCE)
# ============================================

def check_eligibility() -> Dict[str, Any]:
    """
    Reads Agent 4's data from LangGraph state
    
    Returns:
        Agent 4's stored output with eligibility and balance
        
    THIS IS THE PRIMARY DATA SOURCE FOR PLAN GENERATION
    """
    
    return {
        "overall_eligibility": "Eligible",  # Can be: "Eligible", "Not Eligible"
        "eligibility": {
            "CL": {
                "eligible": False,
                "max_days_possible": 0.0
            },
            "PL": {
                "eligible": False,
                "max_days_possible": 0.0
            },
            "LWP": {
                "eligible": True
            }
        },
        "employee_details": {
            "leave_balance": {
                "CL": 0.0,
                "PL": 0.0
            },
            "sandwich_count": 2,  # Can be: 1, 2, 3, etc. or "none" (DYNAMIC)
            "gender": "Male",
            "on_notice_period": False,
            "employee_status": "Trainee",  # Can be: "Confirmed", "probation"
            "team_availability": 80.0
        }
    }


# ============================================
# HELPER: GET ALL AGENTS DATA
# ============================================

def get_all_agents_data() -> Dict[str, Any]:
    """
    Convenience function to get all agents' data at once
    
    Returns:
        Dict with all agents' outputs
    """
    
    return {
        "agent1": parse_intent_and_dates(),
        "agent2": assess_genuineness(),
        "agent3": check_policy(),
        "agent4": check_eligibility()
    }


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING LANGGRAPH STATE ACCESSOR - ACTUAL KEYS")
    print("="*60)
    
    print("\n📥 Agent 1 Data:")
    agent1 = parse_intent_and_dates()
    print(f"  Intent: {agent1['intent_type']}")
    print(f"  Dates: {agent1['start_date']} to {agent1['end_date']}")
    print(f"  Reason: {agent1['reason']}")
    print(f"  Day Type: {agent1['daytype']}")
    
    print("\n📥 Agent 2 Data:")
    agent2 = assess_genuineness()
    print(f"  Score: {agent2['genuineness_assessment']['total_score']}")
    print(f"  Recommendation: {agent2['genuineness_assessment']['recommendation']}")
    
    print("\n📥 Agent 3 Data:")
    agent3 = check_policy()
    print(f"  Max CL: {agent3['max_cl_consecutive_days']} days")
    print(f"  Max PL: {agent3['max_pl_consecutive_days']} days")
    print(f"  Max LWP: {agent3['max_lwp_consecutive_days']} days")
    
    print("\n📥 Agent 4 Data (PRIMARY):")
    agent4 = check_eligibility()
    print(f"  Overall Eligibility: {agent4['overall_eligibility']}")
    print(f"  CL Eligible: {agent4['eligibility']['CL']['eligible']} (Max: {agent4['eligibility']['CL']['max_days_possible']})")
    print(f"  PL Eligible: {agent4['eligibility']['PL']['eligible']} (Max: {agent4['eligibility']['PL']['max_days_possible']})")
    print(f"  LWP Eligible: {agent4['eligibility']['LWP']['eligible']}")
    print(f"  Balances: CL={agent4['employee_details']['leave_balance']['CL']}, PL={agent4['employee_details']['leave_balance']['PL']}")
    print(f"  Sandwich Count: {agent4['employee_details']['sandwich_count']}")
    print(f"  Employee Status: {agent4['employee_details']['employee_status']}")
    print(f"  Team Availability: {agent4['employee_details']['team_availability']}%")
    
    print("\n" + "="*60)
    print("✅ All data retrieved successfully")
    print("="*60)
