from agent_a3_policy_rag import query_leave_policies
import os
import requests


LEAVE_BALANCE_API = os.getenv("LEAVE_BALANCE_API")
EMPLOYEE_DETAILS_API = os.getenv("EMPLOYEE_DETAIL_API")
total_leave_with_sandwich=os.getenv("total_leave_with_sandwich")

def agent_a4_policy_and_eligibility(state: dict, token: str) -> dict:
    """
    Agent A4
    Input:
      - state (from previous agents)
      - token (from login API / LangGraph)
    Output:
      - updated state
    """

    policy_facts = query_leave_policies(state)

    # ---------------- EMPLOYEE CONTEXT ----------------
    headers = {"Authorization": f"Bearer {token}"}

    # Leave balance
    lb_resp = requests.get(
        LEAVE_BALANCE_API, headers=headers, timeout=10, verify=False
    )
    lb_resp.raise_for_status()

    payload = {
    "startDate": state["start_date"],
    "endDate": state["end_date"],
    "leaveType": "CL"
    }
    # total leave
    result= requests.post(total_leave_with_sandwich,json=payload,headers=headers,timeout=10,verify=False)
    
    result.raise_for_status()

    with_sandwich_leave_count = int(result.json()["data"]["noofleaves"])

    balances = {"CL": 0.0, "PL": 0.0}
    for item in lb_resp.json().get("data", []):
        if item.get("leaveTypeCode") in balances:
            balances[item["leaveTypeCode"]] = item.get("balance", 0.0)

    # Employee details
    ed_resp = requests.get(
        EMPLOYEE_DETAILS_API, headers=headers, timeout=10
    )
    ed_resp.raise_for_status()

    emp = ed_resp.json()["data"]["Employee Details"]

    team_size = 10
    team_members_on_leave = 2
    team_availability = ((team_size - team_members_on_leave) / team_size) * 100


    employee_context = {
        "leave_balance": balances,
        "gender": emp["employee_gender"],
        "on_notice_period": emp["notice_period_status"],
        "employee_status": emp["employee_status"],
        "team_availiblity": team_availability
    }

    # ---------------- ELIGIBILITY LOGIC ----------------
    calendar_days = state["calendar_days"]

    cl_balance = balances.get("CL", 0)
    pl_balance = balances.get("PL", 0)

    min_team_required = policy_facts.get("minimum_team_availability_percentage")
    team_ok = True if min_team_required is None else team_availability >= min_team_required

    cl_allowed_key = next(
        (k for k in policy_facts if k.startswith("cl_allowed_for_")), None
    )

    cl_max_days = (
        min(cl_balance, policy_facts.get("max_cl_consecutive_days", 0))
        if cl_allowed_key and policy_facts.get(cl_allowed_key) is not False and team_ok
        else 0
    )

    pl_allowed_key = next(
        (k for k in policy_facts if k.startswith("pl_allowed_for_")), None
    )

    pl_max_days = (
        min(pl_balance, policy_facts.get("max_pl_consecutive_days", 0))
        if pl_allowed_key and policy_facts.get(pl_allowed_key) is not False and team_ok
        else 0
    )

    lwp_allowed = policy_facts.get("lwp_allowed", True)
    max_lwp_days = policy_facts.get("max_lwp_consecutive_days", 8)
    lwp_allowed_for_trainee = policy_facts.get("lwp_allowed_for_trainee", True)

    is_trainee = employee_context["employee_status"] == "Trainee"

    lwp_eligible = (
        lwp_allowed
        and calendar_days <= max_lwp_days
        and team_ok
        and (not is_trainee or lwp_allowed_for_trainee)
    )

    overall_eligible = cl_max_days + pl_max_days >= calendar_days or lwp_eligible

    state["policy_facts"] = policy_facts
    state["employee_context"] = employee_context
    state["eligibility"] = {
        "overall_eligibility": "Eligible" if overall_eligible else "Not Eligible",
        "eligibility": {
            "CL": {"eligible": cl_max_days > 0, "max_days_possible": cl_max_days},
            "PL": {"eligible": pl_max_days > 0, "max_days_possible": pl_max_days},
            "LWP": {"eligible": lwp_eligible},"total_leave":with_sandwich_leave_count
        }
    }

    return state
