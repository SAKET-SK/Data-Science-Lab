"""
AGENT A5: LEAVE PLAN OPTIMIZER - ULTRA-OPTIMIZED V2.0
Production-ready implementation with 100% dynamic constraint handling

KEY IMPROVEMENTS:
1. ✅ Strict validation of ALL agent outputs
2. ✅ Dynamic constraint calculation (min of balance, max_days_possible, policy)
3. ✅ Intelligent plan generation algorithm
4. ✅ Comprehensive edge case handling
5. ✅ Zero invalid plans guaranteed
6. ✅ Better AI prompting with exact constraints
7. ✅ Enhanced fallback logic
8. ✅ Full audit trail logging

Company Policy: Only CL, PL, and LWP (NO SL)
"""

import openai
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

# ============================================
# MODULE-LEVEL STATE CACHE
# ============================================

_cached_plans_state = None
_last_confirmed_plan_id = None


# ============================================
# IMPORTS FROM SERVER LANGGRAPH STATE
# ============================================

def get_agent1_data():
    """Get Agent 1 data from server"""
    from agent_a5_plan_optimizer_helper import parse_intent_and_dates
    return parse_intent_and_dates()


def get_agent2_data():
    """Get Agent 2 data from server"""
    from agent_a5_plan_optimizer_helper import assess_genuineness
    return assess_genuineness()


def get_agent3_data():
    """Get Agent 3 data from server"""
    from agent_a5_plan_optimizer_helper import check_policy
    return check_policy()


def get_agent4_data():
    """Get Agent 4 data from server"""
    from agent_a5_plan_optimizer_helper import check_eligibility
    return check_eligibility()


# ============================================
# HELPER: CALCULATE WORKING DAYS
# ============================================

def calculate_working_days(start_date: str, end_date: str, daytype: str, calendar_days: int) -> float:
    """
    Calculate working days based on daytype
    
    Args:
        start_date: Start date string
        end_date: End date string
        daytype: "fullday", "halfday_1st", "halfday_2nd"
        calendar_days: Total calendar days
    
    Returns:
        Working days (float)
    """
    if "halfday" in daytype.lower():
        if start_date == end_date:
            return 0.5
        else:
            # Multiple days with half-day
            return calendar_days - 0.5
    else:
        return float(calendar_days)


# ============================================
# HELPER: CALCULATE BALANCE AFTER
# ============================================

def calculate_balance_after(leave_breakdown: List[Dict], current_balance: Dict) -> Dict:
    """
    Calculate remaining balance after applying leave plan
    
    Args:
        leave_breakdown: [{"type": "CL", "days": 2.5}, {"type": "PL", "days": 3}]
        current_balance: {"CL": 4.0, "PL": 0.0}
    
    Returns:
        {"CL": 1.5, "PL": 0.0}
    """
    balance_after = {
        "CL": current_balance.get("CL", 0.0),
        "PL": current_balance.get("PL", 0.0)
    }
    
    for leave in leave_breakdown:
        leave_type = leave["type"]
        days = leave["days"]
        
        if leave_type in balance_after:
            balance_after[leave_type] -= days
            balance_after[leave_type] = round(balance_after[leave_type], 1)
    
    return balance_after


# ============================================
# NEW: CALCULATE ACTUAL USABLE LIMITS
# ============================================

def calculate_usable_limits(
    eligibility_data: Dict,
    leave_balance: Dict,
    max_cl_policy: int,
    max_pl_policy: int
) -> Dict[str, float]:
    """
    Calculate ACTUAL usable limits by taking MINIMUM of:
    - Available balance
    - max_days_possible from Agent 4
    - Policy limit from Agent 3
    
    This is the CRITICAL function that ensures dynamic constraint handling
    
    Args:
        eligibility_data: From Agent 4's eligibility
        leave_balance: Current balances
        max_cl_policy: From Agent 3
        max_pl_policy: From Agent 3
    
    Returns:
        {
            "CL": {"eligible": bool, "max_usable": float},
            "PL": {"eligible": bool, "max_usable": float},
            "LWP": {"eligible": bool, "max_usable": float}
        }
    """
    
    cl_eligible = eligibility_data.get("CL", {}).get("eligible", False)
    pl_eligible = eligibility_data.get("PL", {}).get("eligible", False)
    lwp_eligible = eligibility_data.get("LWP", {}).get("eligible", False)
    
    cl_max_possible = eligibility_data.get("CL", {}).get("max_days_possible", 0)
    pl_max_possible = eligibility_data.get("PL", {}).get("max_days_possible", 0)
    
    cl_balance = leave_balance.get("CL", 0.0)
    pl_balance = leave_balance.get("PL", 0.0)
    
    # Calculate CL usable limit (MINIMUM of all constraints)
    cl_max_usable = 0.0
    if cl_eligible:
        cl_max_usable = min(
            cl_balance,           # Available balance
            cl_max_possible,      # Agent 4's eligibility limit
            max_cl_policy         # Agent 3's policy limit
        )
    
    # Calculate PL usable limit (MINIMUM of all constraints)
    pl_max_usable = 0.0
    if pl_eligible:
        pl_max_usable = min(
            pl_balance,           # Available balance
            pl_max_possible,      # Agent 4's eligibility limit
            max_pl_policy         # Agent 3's policy limit
        )
    
    # LWP has no balance constraint (unlimited)
    lwp_max_usable = float('inf') if lwp_eligible else 0.0
    
    return {
        "CL": {
            "eligible": cl_eligible,
            "max_usable": cl_max_usable,
            "balance": cl_balance,
            "max_possible": cl_max_possible,
            "policy_limit": max_cl_policy
        },
        "PL": {
            "eligible": pl_eligible,
            "max_usable": pl_max_usable,
            "balance": pl_balance,
            "max_possible": pl_max_possible,
            "policy_limit": max_pl_policy
        },
        "LWP": {
            "eligible": lwp_eligible,
            "max_usable": lwp_max_usable
        }
    }


# ============================================
# NEW: RULE-BASED INTELLIGENT PLAN GENERATOR
# ============================================

def generate_intelligent_plans(
    duration: float,
    usable_limits: Dict,
    leave_balance: Dict,
    max_lwp_days: int,
    daytype: str,
    reason: str
) -> List[Dict]:
    """
    Generate diverse, valid plans using intelligent rule-based logic
    
    This function GUARANTEES all plans are valid by construction
    
    Args:
        duration: Total days needed
        usable_limits: From calculate_usable_limits()
        leave_balance: Current balances
        max_lwp_days: Max LWP from Agent 3
        daytype: Day type
        reason: Leave reason
    
    Returns:
        List of valid, diverse plans
    """
    
    plans = []
    
    cl_info = usable_limits["CL"]
    pl_info = usable_limits["PL"]
    lwp_info = usable_limits["LWP"]
    
    cl_max = cl_info["max_usable"]
    pl_max = pl_info["max_usable"]
    
    cl_eligible = cl_info["eligible"]
    pl_eligible = pl_info["eligible"]
    lwp_eligible = lwp_info["eligible"]
    
    # ========================================
    # SCENARIO 1: HALF-DAY ONLY (0.5 days)
    # ========================================
    if duration == 0.5:
        if cl_eligible and cl_max >= 0.5:
            plans.append({
                "plan_name": "Plan 1: 0.5 days CL",
                "leave_breakdown": [{"type": "CL", "days": 0.5}],
                "is_recommended": True,
                "explanation": f"Half-day Casual Leave ({daytype}). Quick approval.",
                "balance_after": calculate_balance_after([{"type": "CL", "days": 0.5}], leave_balance)
            })
        
        if pl_eligible and pl_max >= 0.5:
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: 0.5 days PL",
                "leave_breakdown": [{"type": "PL", "days": 0.5}],
                "is_recommended": len(plans) == 0,
                "explanation": f"Half-day Privileged Leave ({daytype}). Preserves CL balance.",
                "balance_after": calculate_balance_after([{"type": "PL", "days": 0.5}], leave_balance)
            })
        
        if lwp_eligible and len(plans) == 0:
            plans.append({
                "plan_name": "Plan 1: 0.5 days LWP",
                "leave_breakdown": [{"type": "LWP", "days": 0.5}],
                "is_recommended": True,
                "explanation": f"Half-day Leave Without Pay ({daytype}).",
                "balance_after": calculate_balance_after([{"type": "LWP", "days": 0.5}], leave_balance)
            })
        
        return plans
    
    # ========================================
    # SCENARIO 2: FULL/MIXED DAYS
    # ========================================
    
    # Plan 1: Use only CL (if possible)
    if cl_eligible and cl_max >= duration:
        plans.append({
            "plan_name": f"Plan {len(plans)+1}: {duration} days CL",
            "leave_breakdown": [{"type": "CL", "days": duration}],
            "is_recommended": True,
            "explanation": "Uses only Casual Leave. Quick approval, no approval needed.",
            "balance_after": calculate_balance_after([{"type": "CL", "days": duration}], leave_balance)
        })
    
    # Plan 2: Use only PL (if possible)
    if pl_eligible and pl_max >= duration:
        plans.append({
            "plan_name": f"Plan {len(plans)+1}: {duration} days PL",
            "leave_breakdown": [{"type": "PL", "days": duration}],
            "is_recommended": len(plans) == 0,
            "explanation": "Uses only Privileged Leave. Preserves CL for emergencies.",
            "balance_after": calculate_balance_after([{"type": "PL", "days": duration}], leave_balance)
        })
    
    # Plan 3: Use only LWP (if no paid leave available)
    if lwp_eligible and duration <= max_lwp_days and cl_max == 0 and pl_max == 0:
        plans.append({
            "plan_name": f"Plan {len(plans)+1}: {duration} days LWP",
            "leave_breakdown": [{"type": "LWP", "days": duration}],
            "is_recommended": len(plans) == 0,
            "explanation": "Leave Without Pay. No paid leave available.",
            "balance_after": calculate_balance_after([{"type": "LWP", "days": duration}], leave_balance)
        })
    
    # Plan 4: Mix CL + PL (if both available and needed)
    if cl_eligible and pl_eligible and cl_max > 0 and pl_max > 0 and (cl_max + pl_max) >= duration:
        # Use maximum CL first, then PL
        cl_use = min(cl_max, duration)
        pl_need = duration - cl_use
        
        if pl_need > 0 and pl_need <= pl_max:
            breakdown = [
                {"type": "CL", "days": cl_use},
                {"type": "PL", "days": pl_need}
            ]
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: {cl_use} days CL + {pl_need} days PL",
                "leave_breakdown": breakdown,
                "is_recommended": len(plans) == 0,
                "explanation": f"Balanced combination using maximum eligible leaves.",
                "balance_after": calculate_balance_after(breakdown, leave_balance)
            })
    
    # Plan 5: CL + LWP (if CL available but insufficient)
    if cl_eligible and lwp_eligible and cl_max > 0 and cl_max < duration:
        lwp_need = duration - cl_max
        
        if lwp_need <= max_lwp_days:
            breakdown = [
                {"type": "CL", "days": cl_max},
                {"type": "LWP", "days": lwp_need}
            ]
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: {cl_max} days CL + {lwp_need} days LWP",
                "leave_breakdown": breakdown,
                "is_recommended": len(plans) == 0,
                "explanation": f"Uses all available CL ({cl_max} days), supplements with unpaid leave.",
                "balance_after": calculate_balance_after(breakdown, leave_balance)
            })
    
    # Plan 6: PL + LWP (if PL available but insufficient)
    if pl_eligible and lwp_eligible and pl_max > 0 and pl_max < duration:
        lwp_need = duration - pl_max
        
        if lwp_need <= max_lwp_days:
            breakdown = [
                {"type": "PL", "days": pl_max},
                {"type": "LWP", "days": lwp_need}
            ]
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: {pl_max} days PL + {lwp_need} days LWP",
                "leave_breakdown": breakdown,
                "is_recommended": len(plans) == 0,
                "explanation": f"Uses all available PL ({pl_max} days), supplements with unpaid leave.",
                "balance_after": calculate_balance_after(breakdown, leave_balance)
            })
    
    # Plan 7: CL + PL + LWP (if both paid leaves available but insufficient)
    if cl_eligible and pl_eligible and lwp_eligible and (cl_max + pl_max) > 0 and (cl_max + pl_max) < duration:
        lwp_need = duration - cl_max - pl_max
        
        if lwp_need <= max_lwp_days:
            breakdown = [
                {"type": "CL", "days": cl_max},
                {"type": "PL", "days": pl_max},
                {"type": "LWP", "days": lwp_need}
            ]
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: {cl_max} CL + {pl_max} PL + {lwp_need} LWP",
                "leave_breakdown": breakdown,
                "is_recommended": len(plans) == 0,
                "explanation": f"Uses all available paid leaves, supplements with {lwp_need} days unpaid leave.",
                "balance_after": calculate_balance_after(breakdown, leave_balance)
            })
    
    # Alternative: PL first, then CL (different preference)
    if cl_eligible and pl_eligible and pl_max > 0 and cl_max > 0 and (pl_max + cl_max) >= duration and len(plans) < 6:
        pl_use = min(pl_max, duration)
        cl_need = duration - pl_use
        
        if cl_need > 0 and cl_need <= cl_max and cl_need != pl_use:  # Avoid duplicate
            breakdown = [
                {"type": "PL", "days": pl_use},
                {"type": "CL", "days": cl_need}
            ]
            plans.append({
                "plan_name": f"Plan {len(plans)+1}: {pl_use} days PL + {cl_need} days CL",
                "leave_breakdown": breakdown,
                "is_recommended": False,
                "explanation": f"Alternative combination prioritizing PL first.",
                "balance_after": calculate_balance_after(breakdown, leave_balance)
            })
    
    return plans[:6]  # Limit to 6 plans


# ============================================
# IMPROVED: AI-POWERED PLAN GENERATION
# ============================================

def generate_diverse_plans_with_ai(
    duration: float,
    usable_limits: Dict,
    leave_balance: Dict,
    max_lwp_days: int,
    reason: str,
    daytype: str
) -> List[Dict]:
    """
    Generate DIVERSE leave plan combinations using AI with STRICT constraints
    
    Args:
        duration: Total days needed (including sandwich)
        usable_limits: From calculate_usable_limits()
        leave_balance: {"CL": 4.0, "PL": 0.0}
        max_lwp_days: Max consecutive LWP allowed
        reason: Leave reason
        daytype: "fullday", "halfday_1st", "halfday_2nd"
    
    Returns:
        List of diverse, validated leave plans
    """
    
    cl_info = usable_limits["CL"]
    pl_info = usable_limits["PL"]
    lwp_info = usable_limits["LWP"]
    
    # Build ultra-precise constraint description
    constraints = []
    
    if cl_info["eligible"]:
        constraints.append(
            f"CL: MAXIMUM {cl_info['max_usable']} days (Balance: {cl_info['balance']}, "
            f"Eligibility Limit: {cl_info['max_possible']}, Policy Limit: {cl_info['policy_limit']})"
        )
    else:
        constraints.append("CL: NOT ELIGIBLE")
    
    if pl_info["eligible"]:
        constraints.append(
            f"PL: MAXIMUM {pl_info['max_usable']} days (Balance: {pl_info['balance']}, "
            f"Eligibility Limit: {pl_info['max_possible']}, Policy Limit: {pl_info['policy_limit']})"
        )
    else:
        constraints.append("PL: NOT ELIGIBLE")
    
    if lwp_info["eligible"]:
        constraints.append(f"LWP: MAXIMUM {max_lwp_days} consecutive days (Unlimited balance)")
    else:
        constraints.append("LWP: NOT ELIGIBLE")
    
    # Half-day handling
    half_day_note = ""
    if duration == 0.5:
        half_day_note = f"""
CRITICAL - HALF-DAY LEAVE ({daytype}):
- Duration is EXACTLY 0.5 days
- Generate ONLY plans with 0.5 days total
- Valid examples: "0.5 CL", "0.5 PL", "0.5 LWP"
- NEVER combine: "0.25 CL + 0.25 PL" is INVALID
"""
    elif duration % 1 == 0.5:
        half_day_note = f"""
MIXED DAYS ({daytype}):
- Total: {duration} days (includes half-day)
- Can use: {int(duration)} + 0.5 days
- Only 0.5 increments allowed
"""
    
    prompt = f"""You are an expert Leave Plan Generator. Create DIVERSE, VALID leave plan combinations.

CRITICAL: Company uses ONLY CL, PL, and LWP (NO SL - Sick Leave).

EMPLOYEE REQUEST:
- Duration: {duration} days
- Reason: {reason}
- Day Type: {daytype}

{half_day_note}

STRICT CONSTRAINTS (YOU MUST OBEY):
{chr(10).join(constraints)}

MANDATORY RULES:
1. Generate 3-6 DIFFERENT combinations
2. Total days MUST = {duration} (EXACTLY)
3. Use ONLY eligible leave types
4. NEVER exceed max_usable limits shown above
5. Use ONLY 0.5 or whole numbers (NO 0.25, 0.75, 1.3, etc.)
6. Mark the best plan with "is_recommended": true
7. If insufficient paid leave, supplement with LWP (if eligible)

EXAMPLES OF VALID PLANS (adapt to actual constraints):
- If CL max = 3, PL max = 2, duration = 5: "3 CL + 2 PL"
- If CL max = 2, PL max = 0, duration = 5: "2 CL + 3 LWP"
- If CL max = 0, PL max = 0, duration = 4: "4 LWP"

OUTPUT FORMAT (JSON only, NO markdown):
[
    {{
        "plan_name": "Plan 1: <description>",
        "leave_breakdown": [
            {{"type": "CL", "days": <number>}},
            {{"type": "PL", "days": <number>}}
        ],
        "is_recommended": true,
        "explanation": "<Why this plan is optimal>"
    }}
]

VALIDATION CHECKLIST (before responding):
✓ Total days = {duration}?
✓ CL days ≤ {cl_info['max_usable']}?
✓ PL days ≤ {pl_info['max_usable']}?
✓ LWP days ≤ {max_lwp_days}?
✓ Only 0.5 or whole numbers?
✓ Only eligible leave types used?
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a leave planning expert. Generate ONLY valid plans using CL, PL, LWP. "
                               "NO SL. Strictly respect all constraints. Use ONLY 0.5 or whole numbers. "
                               "Respond with ONLY valid JSON, no markdown."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content.strip()
        ai_response = ai_response.replace("```json", "").replace("```", "").strip()
        plans = json.loads(ai_response)
        
        # STRICT VALIDATION
        valid_plans = []
        for plan in plans:
            # Check total days
            total_days = sum(leave["days"] for leave in plan["leave_breakdown"])
            if abs(total_days - duration) > 0.01:
                continue
            
            # Check individual constraints
            plan_valid = True
            for leave in plan["leave_breakdown"]:
                leave_type = leave["type"]
                days = leave["days"]
                
                # Check eligibility
                if leave_type == "CL" and not cl_info["eligible"]:
                    plan_valid = False
                    break
                if leave_type == "PL" and not pl_info["eligible"]:
                    plan_valid = False
                    break
                if leave_type == "LWP" and not lwp_info["eligible"]:
                    plan_valid = False
                    break
                
                # Check limits
                if leave_type == "CL" and days > cl_info["max_usable"]:
                    plan_valid = False
                    break
                if leave_type == "PL" and days > pl_info["max_usable"]:
                    plan_valid = False
                    break
                if leave_type == "LWP" and days > max_lwp_days:
                    plan_valid = False
                    break
                
                # Check fractional validity
                if days % 0.5 != 0:
                    plan_valid = False
                    break
            
            if plan_valid:
                plan["balance_after"] = calculate_balance_after(
                    plan["leave_breakdown"],
                    leave_balance
                )
                valid_plans.append(plan)
        
        # If AI produced valid plans, use them
        if valid_plans:
            return valid_plans
        
        # Otherwise, fallback to rule-based
        print("⚠️ AI plans validation failed, using rule-based fallback")
        return generate_intelligent_plans(
            duration, usable_limits, leave_balance, max_lwp_days, daytype, reason
        )
        
    except Exception as e:
        print(f"⚠️ AI Error: {e}, using rule-based fallback")
        return generate_intelligent_plans(
            duration, usable_limits, leave_balance, max_lwp_days, daytype, reason
        )


# ============================================
# PRIMARY FUNCTION: OPTIMIZE LEAVE PLAN
# ============================================

def optimize_leave_plan() -> Dict[str, Any]:
    """
    PRIMARY FUNCTION: Generate diverse leave plans with MAXIMUM accuracy
    
    Process:
    1. Read ALL 4 agents' outputs
    2. Validate critical conditions (recommendation, eligibility, team)
    3. Calculate actual duration (including sandwich)
    4. Calculate usable limits (min of balance, eligibility, policy)
    5. Generate plans using AI + rule-based fallback
    6. Return structured output
    """
    global _cached_plans_state
    
    try:
        print("\n" + "="*70)
        print("📥 AGENT A5 V2: Reading LangGraph State")
        print("="*70)
        
        # ========================================
        # STEP 1: GET ALL AGENTS' DATA
        # ========================================
        agent1_data = get_agent1_data()
        agent2_data = get_agent2_data()
        agent3_data = get_agent3_data()
        agent4_data = get_agent4_data()
        
        print("✅ Retrieved data from Agents 1-4")
        
        # ========================================
        # STEP 2: VALIDATE RECOMMENDATION
        # ========================================
        recommendation = agent2_data.get("genuineness_assessment", {}).get("recommendation", "")
        
        if recommendation.lower() != "approve":
            print(f"❌ Recommendation: '{recommendation}' (not 'approve')")
            return {
                "status": "not_approved",
                "workflow_completed": True,
                "chat_response": f"Leave request not approved. Recommendation: {recommendation}. Please contact HR."
            }
        
        print(f"✅ Recommendation: {recommendation}")
        
        # ========================================
        # STEP 3: VALIDATE TEAM AVAILABILITY
        # ========================================
        employee_details = agent4_data.get("employee_details", {})
        team_availability = employee_details.get("team_availability", 100.0)
        min_team_threshold = agent3_data.get("minimum_team_availability_percentage", 60)
        
        if team_availability < min_team_threshold:
            print(f"❌ Team availability: {team_availability}% < {min_team_threshold}%")
            return {
                "status": "rejected_team_unavailable",
                "workflow_completed": True,
                "chat_response": f"You are not eligible for leave. Team availability ({team_availability}%) is below minimum threshold ({min_team_threshold}%). Please contact administrative authority."
            }
        
        print(f"✅ Team availability: {team_availability}% (threshold: {min_team_threshold}%)")
        
        # ========================================
        # STEP 4: VALIDATE OVERALL ELIGIBILITY
        # ========================================
        overall_eligibility = agent4_data.get("overall_eligibility", "")
        
        if overall_eligibility.lower() != "eligible":
            print(f"❌ Overall eligibility: '{overall_eligibility}'")
            return {
                "status": "not_eligible",
                "workflow_completed": True,
                "chat_response": f"You are not eligible for leave. Reason: {overall_eligibility}. Please contact administrative authority."
            }
        
        print(f"✅ Overall eligibility: {overall_eligibility}")
        
        # ========================================
        # STEP 5: EXTRACT REQUEST DETAILS
        # ========================================
        start_date = agent1_data.get("start_date", "")
        end_date = agent1_data.get("end_date", "")
        reason = agent1_data.get("reason", "")
        calendar_days = agent1_data.get("calendar_days", 0)
        daytype = agent1_data.get("daytype", "fullday")
        
        # Calculate base working days
        base_working_days = calculate_working_days(start_date, end_date, daytype, calendar_days)
        
        # Add sandwich days
        sandwich_count = employee_details.get("sandwich_count", "none")
        actual_duration = base_working_days
        sandwich_message = None
        
        if sandwich_count != "none" and isinstance(sandwich_count, (int, float)) and sandwich_count > 0:
            actual_duration = base_working_days + sandwich_count
            sandwich_message = f"⚠️ {int(sandwich_count)} sandwich day{'s' if sandwich_count > 1 else ''} will also be considered as Leave as per company policy"
            print(f"🍞 Sandwich: +{sandwich_count} days → Total: {actual_duration} days")
        
        print(f"✅ Duration: {actual_duration} days (base: {base_working_days}, sandwich: {sandwich_count})")
        
        # ========================================
        # STEP 6: GET POLICY LIMITS
        # ========================================
        max_cl_policy = agent3_data.get("max_cl_consecutive_days", 3)
        max_pl_policy = agent3_data.get("max_pl_consecutive_days", 3)
        max_lwp_policy = agent3_data.get("max_lwp_consecutive_days", 8)
        
        print(f"✅ Policy Limits: CL={max_cl_policy}, PL={max_pl_policy}, LWP={max_lwp_policy}")
        
        # ========================================
        # STEP 7: CALCULATE USABLE LIMITS (CRITICAL!)
        # ========================================
        eligibility_data = agent4_data.get("eligibility", {})
        leave_balance = employee_details.get("leave_balance", {})
        
        usable_limits = calculate_usable_limits(
            eligibility_data=eligibility_data,
            leave_balance=leave_balance,
            max_cl_policy=max_cl_policy,
            max_pl_policy=max_pl_policy
        )
        
        print(f"✅ Usable Limits:")
        print(f"   CL: max_usable={usable_limits['CL']['max_usable']} (balance={usable_limits['CL']['balance']}, eligible_max={usable_limits['CL']['max_possible']}, policy={usable_limits['CL']['policy_limit']})")
        print(f"   PL: max_usable={usable_limits['PL']['max_usable']} (balance={usable_limits['PL']['balance']}, eligible_max={usable_limits['PL']['max_possible']}, policy={usable_limits['PL']['policy_limit']})")
        print(f"   LWP: eligible={usable_limits['LWP']['eligible']}")
        
        # ========================================
        # STEP 8: CHECK LWP MAXIMUM LIMIT
        # ========================================
        cl_balance = leave_balance.get("CL", 0.0)
        pl_balance = leave_balance.get("PL", 0.0)
        extra_leave_message = None
        
        # If duration > max LWP and no paid leave available
        if actual_duration > max_lwp_policy and cl_balance == 0 and pl_balance == 0:
            print(f"⚠️ Duration ({actual_duration}) > max LWP ({max_lwp_policy}), capping")
            extra_days = actual_duration - max_lwp_policy
            extra_leave_message = f"Only {max_lwp_policy} LWP are allowed. For remaining {extra_days} days please contact with administrative authority"
            actual_duration = max_lwp_policy
        
        # ========================================
        # STEP 9: GENERATE PLANS (AI + Fallback)
        # ========================================
        print(f"\n🤖 Generating plans for {actual_duration} days...")
        
        plans = generate_diverse_plans_with_ai(
            duration=actual_duration,
            usable_limits=usable_limits,
            leave_balance=leave_balance,
            max_lwp_days=max_lwp_policy,
            reason=reason,
            daytype=daytype
        )
        
        if not plans:
            print("❌ No valid plans could be generated")
            return {
                "status": "no_plans",
                "workflow_completed": True,
                "chat_response": "No valid leave plans available. Please contact administrative authority."
            }
        
        print(f"✅ Generated {len(plans)} plans")
        for i, plan in enumerate(plans):
            print(f"   Plan {i+1}: {plan['plan_name']}")
        
        # ========================================
        # STEP 10: CALCULATE FLAGS
        # ========================================
        document_required = (
            reason.lower() == "sickness for self" or
            actual_duration >= 10
        )
        
        approval_flag = actual_duration >= 6
        
        # ========================================
        # STEP 11: CONSTRUCT FINAL OUTPUT
        # ========================================
        result = {
            "leave_request": {
                "start_date": start_date,
                "end_date": end_date,
                "duration": actual_duration,
                "base_duration": base_working_days,
                "sandwich_days": sandwich_count if sandwich_count != "none" else 0,
                "daytype": daytype,
                "reason": reason
            },
            "leave_plan_options": plans,
            "document_required": document_required,
            "approval_flag": approval_flag,
            "awaiting_employee_confirmation": True,
            "workflow_completed": False,
            "status": "plans_generated",
            "generated_at": datetime.now().isoformat()
        }
        
        # Add optional messages
        if sandwich_message:
            result["sandwich_message"] = sandwich_message
        
        if approval_flag:
            result["approval_message"] = "⚠️ This leave needs manager approval"
        
        if document_required:
            result["document_message"] = "📎 Supporting document required"
            result["document_reason"] = "medical_reason" if reason.lower() == "sickness for self" else "duration_exceeds_10_days"
        
        if extra_leave_message:
            result["extra_leave_message"] = extra_leave_message
        
        # CACHE IT
        _cached_plans_state = result
        
        print("\n" + "="*70)
        print("✅ AGENT A5 V2: Plans Generated Successfully")
        print("="*70 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR in optimize_leave_plan:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "workflow_completed": True,
            "chat_response": f"Error generating plans: {str(e)}",
        }

# ============================================
# SEPARATE FUNCTION: CONFIRM LEAVE PLAN
# ============================================

def confirm_leave_plan(plan_id: int) -> Dict[str, Any]:
    """
    SEPARATE FUNCTION: Confirm employee's selected plan
    
    Adds chat_response with plan details
    
    Args:
        plan_id: Index of selected plan (0-based)
    
    Returns:
        Confirmed plan data with chat_response
    """
    global _cached_plans_state, _last_confirmed_plan_id
    
    try:
        print(f"\n{'='*70}")
        print(f"📥 CONFIRM_LEAVE_PLAN: plan_id = {plan_id}")
        print(f"{'='*70}")
        
        # Get current state
        if _cached_plans_state is None:
            print("⚠️ No cached plans, generating...")
            current_state = optimize_leave_plan()
        else:
            print("✅ Using cached plans")
            current_state = _cached_plans_state
        
        # Check for errors
        if current_state.get("error") or current_state.get("status") in [
            "not_approved", "rejected_team_unavailable", "not_eligible", "no_plans"
        ]:
            return current_state
        
        # Validate plan_id
        plans = current_state.get("leave_plan_options", [])
        
        if not plans:
            return {"error": "No plans available", "status": "error"}
        
        if plan_id < 0 or plan_id >= len(plans):
            return {
                "error": f"Invalid plan_id: {plan_id}. Available: 0-{len(plans)-1}",
                "status": "error"
            }
        
        # Store confirmation
        _last_confirmed_plan_id = plan_id
        selected_plan = plans[plan_id]
        
        print(f"✅ Selected: {selected_plan.get('plan_name')}")
        
        # Build chat response
        plan_name = selected_plan["plan_name"]
        leave_breakdown = selected_plan["leave_breakdown"]
        balance_after = selected_plan["balance_after"]
        
        breakdown_text = ", ".join([f"{item['days']} {item['type']}" for item in leave_breakdown])
        balance_text = f"CL: {balance_after['CL']}, PL: {balance_after['PL']}"
        
        chat_response = f"You have selected {plan_name} with leave breakdown as {breakdown_text} and your remaining balance is {balance_text}"
        
        # Construct final output
        result = {
            # "leave_request": current_state.get("leave_request"),
            "selected_plan": {
                "plan_id": plan_id,
                "plan_name": plan_name,
                "leave_breakdown": leave_breakdown,
                "balance_after": balance_after,
                "explanation": selected_plan["explanation"],
                "confirmed_at": datetime.now().isoformat()
            },
            "awaiting_employee_confirmation": False,
            "document_required": current_state.get("document_required"),
            "approval_flag": current_state.get("approval_flag"),
            "workflow_completed": False,
            "status": "confirmed",
            "confirmed_at": datetime.now().isoformat(),
            "chat_response": chat_response
        }
        
        # Preserve messages
        if current_state.get("sandwich_message"):
            result["sandwich_message"] = current_state["sandwich_message"]
        
        if current_state.get("extra_leave_message"):
            result["extra_leave_message"] = current_state["extra_leave_message"]
        
        if current_state.get("approval_message"):
            result["approval_message"] = current_state["approval_message"]
        
        if current_state.get("document_message"):
            result["document_message"] = current_state["document_message"]
            result["document_reason"] = current_state.get("document_reason")
        
        print(f"✅ Plan {plan_id} confirmed")
        print(f"📝 Chat: {chat_response}")
        print(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in confirm_leave_plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "status": "error"}


# ============================================
# HELPER: GET LAST CONFIRMED PLAN
# ============================================

def get_last_confirmed_plan() -> Dict[str, Any]:
    """Get the most recently confirmed plan"""
    global _last_confirmed_plan_id
    
    if _last_confirmed_plan_id is None:
        return {
            "error": "No plan has been confirmed yet",
            "status": "not_confirmed"
        }
    
    return confirm_leave_plan(_last_confirmed_plan_id)


# ============================================
# SEPARATE FUNCTION: CANCEL REQUEST
# ============================================

def cancel_leave_request() -> Dict[str, Any]:
    """Handle cancellation"""
    return {
        "status": "cancelled",
        "cancelled_at": datetime.now().isoformat(),
        "workflow_completed": True,
        "chat_response": "Leave request cancelled by employee"
    }


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING AGENT A5 V2.0 - ULTRA-OPTIMIZED")
    print("="*70)
    
    result = optimize_leave_plan()
    
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
    else:
        req = result.get("leave_request", {})
        print(f"\n📅 Leave Request:")
        print(f"  Dates: {req.get('start_date')} → {req.get('end_date')}")
        print(f"  Duration: {req.get('duration')} days")
        print(f"  Base: {req.get('base_duration')}, Sandwich: {req.get('sandwich_days')}")
        print(f"  Day Type: {req.get('daytype')}")
        print(f"  Reason: {req.get('reason')}")
        
        if result.get("sandwich_message"):
            print(f"\n🍞 {result['sandwich_message']}")
        
        if result.get("approval_message"):
            print(f"⚠️ {result['approval_message']}")
        
        if result.get("document_message"):
            print(f"📎 {result['document_message']}")
        
        print(f"\n📊 Generated {len(result['leave_plan_options'])} Plans:\n")
        
        for i, plan in enumerate(result['leave_plan_options']):
            star = "⭐" if plan.get('is_recommended') else "  "
            print(f"{star} {plan['plan_name']}")
            print(f"   Breakdown: {plan['leave_breakdown']}")
            print(f"   Balance After: {plan['balance_after']}")
            print(f"   Explanation: {plan['explanation']}")
            
            # Validate
            total = sum(leave['days'] for leave in plan['leave_breakdown'])
            if abs(total - req.get('duration', 0)) > 0.01:
                print(f"   ⚠️ WARNING: Total mismatch! {total} != {req.get('duration')}")
            
            for leave in plan['leave_breakdown']:
                if leave['days'] % 0.5 != 0:
                    print(f"   ⚠️ WARNING: Invalid fraction {leave['days']}")
            
            print()
    
    print("="*70)
