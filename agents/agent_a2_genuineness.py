# agent_a2_genuineness.py
# --------------------------------------------------
# Genuineness/Pattern Analyzer
# --------------------------------------------------

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import httpx
import statistics
from collections import Counter
import calendar
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= CONFIG =================
class Config:
    LEAVE_API = "https://devmcdphcmplatform.omfysgroup.com/user/leaves/showleavereport"

    WEIGHTS = {
        "reason": 0.30,
        "timing": 0.25,
        "duration": 0.20,
        "notice": 0.15,
        "behaviour": 0.10
    }

    LAST_MINUTE = 2
    WELL_PLANNED = 15
    MONTH_END_DAYS = 7
    SUDDEN_CHANGE_RATIO = 1.8

config = Config()

# ================= MODELS =================
class CurrentRequest(BaseModel):
    """Current leave request details from Intent Parser"""
    reason_category: str
    start_date: str
    end_date: str
    application_date: str

class GenuinenessState(BaseModel):
    """State model for genuineness analysis"""
    analysis_complete: bool = False
    analysis_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Metadata
    employee_id: Optional[str] = None
    session_id: Optional[str] = None
    username: Optional[str] = None

# ================= HELPERS =================
def parse_date(date_str: str) -> datetime:
    """Parse date string in multiple formats"""
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")

CANONICAL_REASONS = {
    "family function": "Family function",
    "going outstation": "Going Outstation",
    "sickness for self": "Sickness for Self",
    "sickness of family member": "Sickness of family member",
    "death of relatives": "Death of Relatives",
    "death of family member": "Death of family member",
    "other": "Other",
}

def normalize_reason(raw_reason: str) -> str:
    """Normalize reason to canonical form"""
    if not raw_reason:
        return "Other"
    return CANONICAL_REASONS.get(raw_reason.strip().lower(), "Other")

# ================= API CALLS =================
async def get_leaves(token: str, start: str, end: str) -> Dict[str, Any]:
    """Fetch leave history from API using token"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            r = await client.post(
                config.LEAVE_API,
                json={"start_date": start, "end_date": end},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            
            if r.status_code != 200:
                logger.error(f"Leave API returned status {r.status_code}")
                return {"leaves": [], "counts": {}}
            
            data = r.json().get("data", {})
            return {
                "leaves": data.get("leaveReport", []),
                "counts": data.get("count", {})
            }
    except httpx.TimeoutException:
        logger.error("Leave API request timed out")
        return {"leaves": [], "counts": {}}
    except Exception as e:
        logger.error(f"Error fetching leaves: {str(e)}")
        return {"leaves": [], "counts": {}}

# ================= FACTOR 1: REASON FREQUENCY =================
def calc_reason_freq(leaves: List[Dict], curr_reason: str) -> Dict:
    """Calculate reason frequency score"""
    total = len(leaves)
    if total == 0:
        return {"raw_score": 95, "flags": []}

    norm = normalize_reason(curr_reason)
    counts = Counter(normalize_reason(l.get("c_reason_category", "")) for l in leaves)
    rate = counts.get(norm, 0) / total

    if rate < 0.05: score = 95
    elif rate < 0.10: score = 85
    elif rate < 0.20: score = 70
    elif rate < 0.30: score = 50
    else: score = 30

    flags = ["REASON_OVERUSED"] if rate > 0.20 else []

    return {
        "raw_score": score,
        "similar_reason_count": counts.get(norm, 0),
        "frequency_rate": round(rate, 3),
        "flags": flags
    }

# ================= FACTOR 2: TIMING PATTERNS =================
def calc_timing(leaves: List[Dict], curr_start: datetime) -> Dict:
    """Calculate timing pattern score"""
    total = len(leaves)
    if total == 0:
        return {"raw_score": 95, "flags": []}

    sandwich = 0
    month_end = 0

    for l in leaves:
        try:
            sd = parse_date(l["start_date"])
            weekday = l.get("c_leave_start_weekday")

            # Sandwich leave: Friday or Monday
            if weekday in ("Friday", "Monday"):
                sandwich += 1

            # Month-end (last 7 days)
            last_day = calendar.monthrange(sd.year, sd.month)[1]
            if sd.day >= last_day - (config.MONTH_END_DAYS - 1):
                month_end += 1
        except Exception as e:
            logger.warning(f"Error parsing leave date: {e}")
            continue

    sandwich_rate = sandwich / total if total > 0 else 0
    month_end_rate = month_end / total if total > 0 else 0

    flags = []
    if sandwich_rate > 0.20:
        flags.append("HIGH_SANDWICH_PATTERN")
    if month_end_rate > 0.25:
        flags.append("MONTH_END_CLUSTERING")

    score = 95
    if flags:
        score = 75
    if len(flags) > 1:
        score = 60

    # Current request flags
    last_day = calendar.monthrange(curr_start.year, curr_start.month)[1]
    if curr_start.strftime("%A") in ("Friday", "Monday"):
        flags.append("CURRENT_SANDWICH")
    if curr_start.day >= last_day - (config.MONTH_END_DAYS - 1):
        flags.append("CURRENT_MONTH_END")

    return {
        "raw_score": score,
        "sandwich_rate": round(sandwich_rate, 3),
        "month_end_rate": round(month_end_rate, 3),
        "flags": flags
    }

# ================= FACTOR 3: DURATION CONSISTENCY =================
def calc_duration(leaves: List[Dict], curr_dur: int, curr_reason: str) -> Dict:
    """Calculate duration consistency score"""
    if not leaves:
        return {"raw_score": 95, "flags": []}

    durs = [l["c_duration_days"] for l in leaves if l.get("c_duration_days")]
    if not durs:
        return {"raw_score": 95, "flags": []}
    
    avg = statistics.mean(durs)
    std = statistics.stdev(durs) if len(durs) > 1 else 0

    reason_durs = [
        l["c_duration_days"]
        for l in leaves
        if normalize_reason(l.get("c_reason_category", "")) == normalize_reason(curr_reason)
    ]
    base = statistics.mean(reason_durs) if reason_durs else avg
    deviation = abs(curr_dur - base)

    if deviation <= std: score = 95
    elif deviation <= 2 * std: score = 75
    elif deviation <= 3 * std: score = 50
    else: score = 25

    flags = ["DURATION_OUTLIER"] if score <= 50 else []

    return {
        "raw_score": score,
        "duration_deviation": round(deviation, 2),
        "flags": flags
    }

# ================= FACTOR 4: ADVANCE NOTICE =================
def calc_notice(leaves: List[Dict], curr_adv: int) -> Dict:
    """Calculate advance notice score"""
    if not leaves:
        score = 90 if curr_adv >= config.WELL_PLANNED else 60
        return {"raw_score": score, "flags": []}

    advs = [l["c_advance_notice_days"] for l in leaves if l.get("c_advance_notice_days") is not None]
    if not advs:
        score = 90 if curr_adv >= config.WELL_PLANNED else 60
        return {"raw_score": score, "flags": []}
    
    hist_avg = statistics.mean(advs)
    last_minute_rate = sum(1 for a in advs if a <= config.LAST_MINUTE) / len(advs)

    if curr_adv >= config.WELL_PLANNED:
        score = 95 if curr_adv >= hist_avg else 85
    elif curr_adv > config.LAST_MINUTE:
        score = 70
    else:
        score = 50 if last_minute_rate < 0.2 else 30

    flags = ["LAST_MINUTE_REQUEST"] if curr_adv <= config.LAST_MINUTE else []

    return {"raw_score": score, "flags": flags}

# ================= FACTOR 5: BEHAVIOUR CONSISTENCY =================
def calc_behaviour(leaves: List[Dict], counts: Dict) -> Dict:
    """Calculate behaviour consistency score"""
    if not leaves:
        return {"raw_score": 95, "flags": []}

    # Approval / cancellation
    total = sum(counts.values()) if counts else len(leaves)
    if total == 0:
        return {"raw_score": 95, "flags": []}

    approved = counts.get("approved", 0)
    rejected = counts.get("rejected", 0)
    cancelled = counts.get("cancelled", 0)

    approval_rate = round(approved / total, 3) if total else 0
    rejection_rate = round(rejected / total, 3) if total else 0
    cancellation_rate = round(cancelled / total, 3) if total else 0

    # Gap analysis
    try:
        starts = sorted(parse_date(l["start_date"]) for l in leaves)
        gaps = [(starts[i] - starts[i-1]).days for i in range(1, len(starts))]

        avg_gap = statistics.mean(gaps) if gaps else 0
        gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
    except Exception as e:
        logger.warning(f"Error calculating gaps: {e}")
        avg_gap = 0
        gap_std = 0

    # Sudden change (last 3 months)
    try:
        starts = sorted(parse_date(l["start_date"]) for l in leaves)
        cutoff = max(starts) - timedelta(days=90)
        recent = [l for l in leaves if parse_date(l["start_date"]) >= cutoff]

        hist_months = 12
        recent_months = 3

        hist_count_avg = total / hist_months
        recent_count_avg = len(recent) / recent_months

        hist_dur_avg = sum(l.get("c_duration_days", 0) for l in leaves) / hist_months
        recent_dur_avg = sum(l.get("c_duration_days", 0) for l in recent) / recent_months if recent else 0

        sudden_freq = recent_count_avg > hist_count_avg * config.SUDDEN_CHANGE_RATIO
        sudden_dur = recent_dur_avg > hist_dur_avg * config.SUDDEN_CHANGE_RATIO
    except Exception as e:
        logger.warning(f"Error calculating sudden changes: {e}")
        sudden_freq = False
        sudden_dur = False

    flags = []
    if sudden_freq:
        flags.append("SUDDEN_FREQUENCY_INCREASE")
    if sudden_dur:
        flags.append("SUDDEN_DURATION_INCREASE")

    if approval_rate >= 0.95 and not flags:
        score = 95
    elif approval_rate >= 0.85:
        score = 80
    elif approval_rate >= 0.70:
        score = 65
    else:
        score = 40

    return {
        "raw_score": score,
        "approval_rate": approval_rate,
        "rejection_rate": rejection_rate,
        "cancellation_rate": cancellation_rate,
        "avg_gap_days": round(avg_gap, 2),
        "gap_std_dev": round(gap_std, 2),
        "flags": flags
    }

# ================= HELPER FUNCTIONS =================
def compute_common_reasons(leaves: List[Dict]) -> List[Dict]:
    """Compute most common leave reasons"""
    counts = Counter(
        normalize_reason(l.get("c_reason_category", "Other"))
        for l in leaves
    )
    return [{"reason": k, "count": v} for k, v in counts.most_common()]

def approval_stats(leaves: List[Dict]) -> Dict:
    """Calculate approval statistics"""
    total = len(leaves)
    if total == 0:
        return {
            "total_approved": 0,
            "approval_rate": 0,
            "total_rejections": 0,
            "rejection_rate": 0,
            "cancelled_leaves": 0,
            "cancellation_rate": 0
        }
    
    approved = sum(1 for l in leaves if "approved" in l.get("status", "").lower())
    rejected = sum(1 for l in leaves if "reject" in l.get("status", "").lower())
    cancelled = sum(1 for l in leaves if "cancelled" in l.get("status", "").lower())

    return {
        "total_approved": approved,
        "approval_rate": round(approved / total, 3),
        "total_rejections": rejected,
        "rejection_rate": round(rejected / total, 3),
        "cancelled_leaves": cancelled,
        "cancellation_rate": round(cancelled / total, 3)
    }

# ================= CORE ANALYSIS =================
async def perform_analysis(
    token: str,
    emp_code: str,
    curr: CurrentRequest
) -> Dict[str, Any]:
    """
    Perform the core genuineness analysis
    """
    try:
        # Parse dates
        end = parse_date(curr.end_date)
        start = end - timedelta(days=365)
        
        # Fetch historical leaves
        leave_data = await get_leaves(
            token, 
            start.strftime("%Y-%m-%d"), 
            end.strftime("%Y-%m-%d")
        )
        leaves = leave_data["leaves"]
        counts = leave_data["counts"]

        logger.info(f"Fetched {len(leaves)} historical leaves for {emp_code}")

        # Calculate current request metrics
        curr_start = parse_date(curr.start_date)
        curr_dur = (parse_date(curr.end_date) - curr_start).days + 1
        curr_adv = (curr_start - parse_date(curr.application_date)).days

        # Calculate all factors
        f1 = calc_reason_freq(leaves, curr.reason_category)
        f2 = calc_timing(leaves, curr_start)
        f3 = calc_duration(leaves, curr_dur, curr.reason_category)
        f4 = calc_notice(leaves, curr_adv)
        f5 = calc_behaviour(leaves, counts)

        factors = {
            "reason": f1, 
            "timing": f2, 
            "duration": f3, 
            "notice": f4, 
            "behaviour": f5
        }

        # Calculate weighted total score
        total = sum(factors[k]["raw_score"] * config.WEIGHTS[k] for k in factors)

        # Determine category and recommendation
        if total >= 85:
            category, rec = "Highly genuine", "approve"
        elif total >= 60:
            category, rec = "Moderately genuine", "approve"
        elif total >= 40:
            category, rec = "Low genuineness", "approve"
        else:
            category, rec = "Extremely suspicious", "reject"

        # Compute additional statistics
        common_reasons = compute_common_reasons(leaves)
        stats = approval_stats(leaves)

        # Build complete analysis result
        return {
            "employee_id": emp_code,
            "analysis_period": "12 months",

            "current_request": {
                "reason": curr.reason_category.lower(),
                "start_date": curr.start_date,
                "end_date": curr.end_date,
                "duration_days": curr_dur,
                "advance_notice_days": curr_adv,
                "has_attachment": False,
                "attachment_type": None
            },

            "factor_1_reason_frequency": {
                "weight": config.WEIGHTS["reason"],
                "similar_reason_count": f1["similar_reason_count"],
                "total_leaves": len(leaves),
                "frequency_rate": f1["frequency_rate"],
                "common_reasons": common_reasons,
                "current_reason_normalized": normalize_reason(curr.reason_category),
                "is_overused": "REASON_OVERUSED" in f1["flags"],
                "raw_score": f1["raw_score"]
            },

            "factor_2_timing_patterns": {
                "weight": config.WEIGHTS["timing"],
                "total_leaves": len(leaves),
                "sandwich_leaves": {
                    "count": int(f2["sandwich_rate"] * len(leaves)),
                    "sandwich_rate": f2["sandwich_rate"]
                },
                "month_end_rate": f2["month_end_rate"],
                "current_request_flags": {
                    "is_sandwich": "CURRENT_SANDWICH" in f2["flags"],
                    "is_month_end": "CURRENT_MONTH_END" in f2["flags"]
                },
                "raw_score": f2["raw_score"]
            },

            "factor_3_duration_consistency": {
                "weight": config.WEIGHTS["duration"],
                "current_duration": curr_dur,
                "duration_deviation": f3["duration_deviation"],
                "is_abnormal": "DURATION_OUTLIER" in f3["flags"],
                "justification_needed": f3["raw_score"] < 60,
                "raw_score": f3["raw_score"]
            },

            "factor_4_advance_notice": {
                "weight": config.WEIGHTS["notice"],
                "advance_days": curr_adv,
                "current_is_last_minute": "LAST_MINUTE_REQUEST" in f4["flags"],
                "raw_score": f4["raw_score"]
            },

            "factor_5_behaviour_consistency": {
                "weight": config.WEIGHTS["behaviour"],
                "approval_rate": stats["approval_rate"],
                "rejection_rate": stats["rejection_rate"],
                "cancellation_rate": stats["cancellation_rate"],
                "pattern_stability": {
                    "consistent_leave_spacing": f5["avg_gap_days"] > 7,
                    "behavioral_anomaly_detected": len(f5["flags"]) > 0,
                    "stability_score": round(1 - (len(f5["flags"]) * 0.15), 2)
                },
                "raw_score": f5["raw_score"]
            },

            "additional_context": {
                "approval_history": {
                    "total_approved": counts.get("approved", 0),
                    "approval_rate": f5["approval_rate"]
                },
                "rejection_history": {
                    "total_rejections": counts.get("rejected", 0),
                    "rejection_rate": f5["rejection_rate"]
                },
                "cancellation_pattern": {
                    "cancelled_leaves": counts.get("cancelled", 0),
                    "cancellation_rate": f5["cancellation_rate"]
                }
            },

            "calculated_score": {
                "factor_1_weighted": round(f1["raw_score"] * config.WEIGHTS["reason"], 2),
                "factor_2_weighted": round(f2["raw_score"] * config.WEIGHTS["timing"], 2),
                "factor_3_weighted": round(f3["raw_score"] * config.WEIGHTS["duration"], 2),
                "factor_4_weighted": round(f4["raw_score"] * config.WEIGHTS["notice"], 2),
                "factor_5_weighted": round(f5["raw_score"] * config.WEIGHTS["behaviour"], 2),
                "total_score": round(total, 2),
                "score_category": category,
                "recommendation": rec,
            }
        }

    except Exception as e:
        logger.exception(f"Error in perform_analysis: {str(e)}")
        raise

# ================= MAIN FUNCTION FOR LANGGRAPH =================
async def assess_genuineness(
    leave_details: Dict[str, Any],
    login_response: Dict[str, Any],
    current_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function to assess leave genuineness for LangGraph integration.
    
    Args:
        leave_details: Leave request details (from Intent Parser output)
            Expected keys: start_date, end_date, reason, application_date
        login_response: Full login response from common login API
            Expected keys: session_id, empCode, token, username
        current_state: Current state from LangGraph (optional)
        
    Returns:
        Dictionary containing genuineness analysis state
    """
    
    # Extract login info
    session_id = login_response.get("session_id")
    emp_code = login_response.get("empCode")
    token = login_response.get("token")
    username = login_response.get("username")
    
    logger.info(f"Assessing genuineness for {username} ({emp_code})")
    
    # Initialize state
    if current_state:
        state = GenuinenessState(**current_state)
    else:
        state = GenuinenessState(
            employee_id=emp_code,
            session_id=session_id,
            username=username
        )
    
    # Ensure metadata is always present
    state.employee_id = emp_code
    state.session_id = session_id
    state.username = username
    
    try:
        # Validate required fields in leave_details
        required_fields = ["start_date", "end_date", "reason"]
        missing_fields = [f for f in required_fields if not leave_details.get(f)]
        
        if missing_fields:
            state.error = f"Missing required leave details: {', '.join(missing_fields)}"
            state.error_code = "MISSING_LEAVE_DETAILS"
            state.analysis_complete = False
            logger.error(state.error)
            return state.dict()
        
        # Get application_date (use current date if not provided)
        application_date = leave_details.get(
            "application_date",
            datetime.now().strftime("%Y-%m-%d")
        )
        
        # Prepare current request
        curr = CurrentRequest(
            reason_category=leave_details["reason"],
            start_date=leave_details["start_date"],
            end_date=leave_details["end_date"],
            application_date=application_date
        )
        
        # Validate token
        if not token:
            state.error = "Authentication token not found in login response"
            state.error_code = "MISSING_TOKEN"
            state.analysis_complete = False
            logger.error(state.error)
            return state.dict()
        
        # Perform analysis
        logger.info(f"Starting genuineness analysis for {emp_code}")
        analysis_result = await perform_analysis(token, emp_code, curr)
        
        # Update state with results
        state.analysis_complete = True
        state.analysis_result = analysis_result
        state.error = None
        state.error_code = None
        
        logger.info(
            f"Analysis complete: Score={analysis_result['calculated_score']['total_score']}, "
            f"Category={analysis_result['calculated_score']['score_category']}"
        )
        
                # ---------------- OUTPUT NORMALIZATION ----------------

        if state.analysis_complete and state.analysis_result:
            total_score = state.analysis_result["calculated_score"]["total_score"]
            recommendation = state.analysis_result["calculated_score"]["recommendation"]

            return {
                "genuineness_assessment": {
                    "total_score": total_score,
                    "recommendation": recommendation
                },
                "workflow_completed": True,
                "status": "completed",
                "chat_response": "Request validated. Checking eligibility."
            }

        # If analysis is still in progress or failed
        return {
            "genuineness_assessment": None,
            "workflow_completed": False,
            "status": "processing" if not state.error else "failed",
            "chat_response": (
                "Something went wrong"
                if not state.error
                else state.error
            )
        }

        
    except ValueError as e:
        state.error = f"Invalid date format: {str(e)}"
        state.error_code = "INVALID_DATE_FORMAT"
        state.analysis_complete = False
        logger.error(state.error)
        return state.dict()
        
    except httpx.HTTPError as e:
        state.error = f"API communication error: {str(e)}"
        state.error_code = "API_ERROR"
        state.analysis_complete = False
        logger.error(state.error)
        return state.dict()
        
    except Exception as e:
        state.error = f"Unexpected error during analysis: {str(e)}"
        state.error_code = "ANALYSIS_ERROR"
        state.analysis_complete = False
        logger.exception("Unexpected error in assess_genuineness")
        return state.dict()


