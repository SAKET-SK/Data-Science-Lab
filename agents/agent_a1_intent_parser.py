# agent_a1_intent_parser.py
# --------------------------------------------------
# Intent Parser Agent 
# --------------------------------------------------

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Literal, Any
from pydantic import BaseModel, Field
import os
import re
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# ==================================================
# CONFIG
# ==================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MEDICAL_DOC_THRESHOLD = 10

CANONICAL_REASONS = [
    "Family function",
    "Going Outstation",
    "Sickness for Self",
    "Sickness of family member",
    "Death of Relatives",
    "Death of family member",
    "Other",
]

# import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s"
# )

# logger = logging.getLogger("intent-parser")

# ==================================================
# SCHEMAS
# ==================================================

class LoginResponse(BaseModel):
    """Login response structure from common login API"""
    session_id: str
    empCode: str
    roles: List[str]
    token: str
    username: str
    message: str


class LeaveState(BaseModel):
    """Leave application state"""
    intent_type: Optional[str] = None  
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    calendar_days: Optional[int] = None
    medical_document: Optional[bool] = None
    awaiting_field: Optional[Literal["start_date", "end_date", "reason"]] = None
    preview_confirmed: bool = False
    application_date: Optional[str] = None
    parsing_status: str

    daytype: Optional[
        Literal["fullday", "halfday_1st", "halfday_2nd"]
    ] = None

    missing_fields: List[str] = Field(default_factory=list)
    chat_response: str = ""
    
    session_id: Optional[str] = None
    empCode: Optional[str] = None
    username: Optional[str] = None


class ExtractionResult(BaseModel):
    """LLM extraction result"""
    intent_type: Optional[
        Literal["apply_leave", "update_leave", "cancel_leave"]
    ] = None
    
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    reason: Optional[
        Literal[
            "Family function",
            "Going Outstation",
            "Sickness for Self",
            "Sickness of family member",
            "Death of Relatives",
            "Death of family member",
            "Other"
        ]
    ] = None

    medical_document: Optional[bool] = None

    intent_to_change: Optional[
        Literal["start_date", "end_date", "reason"]
    ] = None

    confirmation: Optional[
        Literal["yes", "no"]
    ] = None

    daytype: Optional[
        Literal["fullday", "halfday_1st", "halfday_2nd"]
    ] = None
# ==================================================
# DATE HELPERS
# ==================================================

def validate_iso(date_str: str) -> bool:
    """Validate ISO date format"""
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def calculate_duration(start_iso: str, end_iso: str) -> int:
    """
    Calculate inclusive leave duration in days.
    """
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    return (end - start).days + 1


WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def next_weekday(reference: datetime, weekday: int) -> datetime:
    """Return next occurrence of a weekday"""
    days_ahead = weekday - reference.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return reference + timedelta(days=days_ahead)


def parse_human_date_range(text: str, reference: datetime):
    t = text.lower().strip()

    start = None
    end = None

    # --------------------------------------------------
    # RANGE EXPRESSIONS: "from X to Y"
    # --------------------------------------------------
    if "from" in t and "to" in t:

        if "tomorrow" in t:
            start = reference + timedelta(days=1)

        if "day after tomorrow" in t:
            end = reference + timedelta(days=2)

        if "today" in t:
            start = reference

    # --------------------------------------------------
    # SINGLE RELATIVE DAYS (only if range not detected)
    # --------------------------------------------------
    if start is None and end is None:

        if "day after tomorrow" in t:
            start = reference + timedelta(days=2)
            end = start

        elif "tomorrow" in t:
            start = reference + timedelta(days=1)
            end = start

        elif "today" in t:
            start = reference
            end = start

    # --------------------------------------------------
    # DURATION: next / upcoming N days
    # --------------------------------------------------
    m = re.search(r"(next|upcoming)\s+(\d+)\s+days", t)
    if m:
        days = int(m.group(2))
        start = reference
        end = reference + timedelta(days=days - 1)

    m = re.search(r"for\s+(\d+)\s+days", t)
    if m:
        days = int(m.group(1))
        start = reference
        end = reference + timedelta(days=days - 1)

    # --------------------------------------------------
    # FINAL SAFETY
    # --------------------------------------------------
    if start and not end:
        end = start

    if start and end:
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    return None, None

# ==================================================
# INTENT EXTRACTION (LLM)
# ==================================================

llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    api_key=OPENAI_API_KEY
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an intent extraction and classification engine for a leave management system.

        Tasks:
        
        0. Detect intent_type (NEW - CRITICAL):
           - "apply_leave": User wants to apply for a new leave
             Examples: "apply my leave", "I want to take leave", "request leave", "book leave"
           
           - "update_leave": User wants to change an existing field
             Examples: "change the start date", "update my reason", "modify end date"
           
           - "cancel_leave": User wants to cancel the entire process
             Examples: "cancel", "stop", "don't want to apply", "forget it", "never mind"
           
           Default to "apply_leave" if user is providing leave details and hasn't explicitly asked to cancel or update.

        1. Extract start_date and end_date if present.

        DATE RULES (VERY IMPORTANT):
        - TODAY'S DATE IS: {current_date}
        - Convert ALL dates to ISO format: YYYY-MM-DD
        - Understand relative dates based on TODAY ({current_date}):
          - "tomorrow" = add 1 day to {current_date}
          - "day after tomorrow" = add 2 days to {current_date}
          - "next monday" = find next occurrence of Monday after {current_date}
          - "next week" = add 7 days to {current_date}
        - If user gives exact date → convert to ISO

        Example (if today is 2026-01-12):
        User: "apply my leave for tomorrow"
        → intent_type = "apply_leave", start_date = "2026-01-13", end_date = "2026-01-13"
        
        User: "leave from tomorrow to day after tomorrow"
        → intent_type = "apply_leave", start_date = "2026-01-13", end_date = "2026-01-14"

        DO NOT return raw text like "tomorrow" or "next monday".
        Always return ISO dates or null.

        2. Classify the user's reason into EXACTLY ONE of the following:
           - Family function
           - Going Outstation
           - Sickness for Self
           - Sickness of family member
           - Death of Relatives
           - Death of family member
           - Other

        Rules for reason classification:
        - Use semantic meaning, not keywords.
        - If the reason clearly fits ONE category, return it.
        - If the reason could fit MULTIPLE categories, return null.
        - If no reason is mentioned, return null.

        3. Detect intent_to_change only if the user wants to update a field.
        Allowed values: start_date, end_date, reason.

        4. Detect confirmation (CRITICAL - MOST IMPORTANT):
           Examples of YES:
           - "yes" → confirmation = "yes"
           - "YES" → confirmation = "yes"
           - "Yes" → confirmation = "yes"
           - "yeah" → confirmation = "yes"
           - "ok" → confirmation = "yes"
           - "confirm" → confirmation = "yes"
           - "correct" → confirmation = "yes"
           
           Examples of NO:
           - "no" → confirmation = "no"
           - "NO" → confirmation = "no"
           - "change it" → confirmation = "no"
           - "not correct" → confirmation = "no"
           
           If the message is ONLY a confirmation word, you MUST detect it.

        5. Extract medical_document:
           - If user confirms they have/will attach document → true
           - If user says they don't have it → false
           - Otherwise → null

        Return null for anything not present or unclear.

        6. Extract daytype (leave duration type):

        Allowed values:
        - fullday
        - halfday_1st
        - halfday_2nd

        Examples:
        - "first half", "morning half", "half day first half" → halfday_1st
        - "second half", "afternoon", "half day second half" → halfday_2nd
        - If user does not mention → null


        """
    ),
    ("human", "{input}")
])


def extract_intent(text: str) -> ExtractionResult:
    structured_llm = llm.with_structured_output(ExtractionResult)
    chain = prompt | structured_llm

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    result = chain.invoke({"input": text, "current_date": current_date})

    # ─────────────────────────────────────
    # HARD DATE NORMALIZATION (FINAL AUTHORITY)
    # ─────────────────────────────────────
    start, end = parse_human_date_range(text, now)

    if start:
        result.start_date = start
        result.end_date = end

    return result



# ==================================================
# BUSINESS VALIDATION
# ==================================================

def validate_state(state: LeaveState) -> LeaveState:
    """
    Validates business rules for leave application.
    Assumes dates are already valid ISO strings.
    """

    # ─────────────────────────────────────────────
    # REQUIRED FIELD CHECK
    # ─────────────────────────────────────────────
    missing = []

    if not state.start_date:
        missing.append("start_date")
    if not state.end_date:
        missing.append("end_date")
    if not state.reason:
        missing.append("reason")


    if missing:
        state.parsing_status = "incomplete"
        state.missing_fields = missing
        state.chat_response = f"Please provide: {', '.join(missing)}"
        return state

    # ─────────────────────────────────────────────
    # DURATION CALCULATION
    # ─────────────────────────────────────────────
    duration = calculate_duration(state.start_date, state.end_date)
    state.calendar_days = duration

    if duration < 1:
        state.parsing_status = "incomplete"
        state.chat_response = "End date cannot be before start date."
        return state


    # ─────────────────────────────────────────────
    # HALF DAY TIME RULES (ONLY FOR TODAY)
    # ─────────────────────────────────────────────
    if state.daytype in {"halfday_1st", "halfday_2nd"}:
        today = datetime.now().date()
        start_date = datetime.fromisoformat(state.start_date).date()

        if start_date == today:
            now_time = datetime.now().time()

            if state.daytype == "halfday_1st" and now_time >= datetime.strptime("09:30", "%H:%M").time():
                state.parsing_status = "incomplete"
                state.missing_fields = ["daytype"]
                state.chat_response = (
                    "First half leave for today cannot be applied after 9:30 AM. "
                    "You can apply second half or full day."
                )
                return state

            if state.daytype == "halfday_2nd" and now_time >= datetime.strptime("13:30", "%H:%M").time():
                state.parsing_status = "incomplete"
                state.missing_fields = ["daytype"]
                state.chat_response = (
                    "Second half leave for today cannot be applied after 1:30 PM."
                )
                return state

    # ─────────────────────────────────────────────
    # MEDICAL DOCUMENT RULE
    # ─────────────────────────────────────────────
    if (
        state.reason in {"Sickness for Self"}
        and duration > MEDICAL_DOC_THRESHOLD
    ):
        if state.medical_document is not True:
            state.parsing_status = "incomplete"
            state.missing_fields = ["medical_document"]
            state.chat_response = (
                f"Medical certificate is required for medical leave longer than "
                f"{MEDICAL_DOC_THRESHOLD} days. Please attach the document."
            )
            return state

    # ─────────────────────────────────────────────
    # STATE IS VALID
    # ─────────────────────────────────────────────
    state.parsing_status = "complete"
    state.missing_fields = []
    state.chat_response = ""

    return state


# ==================================================
# MAIN FUNCTION FOR LANGGRAPH
# ==================================================

def parse_intent_and_dates(
    user_message: str,
    login_response: Dict[str, Any],
    current_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function to parse intent and dates for LangGraph integration.
    
    Args:
        user_message: The user's input message
        login_response: Full login response from common login API
        current_state: Current state from LangGraph (optional)
        
    Returns:
        Dictionary containing updated state
    """
    
    # Extract session info from login response
    session_id = login_response.get("session_id")
    empCode = login_response.get("empCode")
    username = login_response.get("username")

    application_date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Session={session_id} | User={username} | Message={user_message}")
    
    # Initialize or load state from LangGraph
    if current_state:
        state = LeaveState(**current_state)
    else:
        state = LeaveState(
            parsing_status="incomplete",
            missing_fields=["start_date", "end_date", "reason"],
            session_id=session_id,
            empCode=empCode,
            username=username,
            application_date=application_date 
        )
    
    # Ensure session info is always present
    state.session_id = session_id
    state.empCode = empCode
    state.username = username

    if not state.application_date:
        state.application_date = application_date

    # Extract intent using LLM
    extracted = extract_intent(user_message)
    logger.info(f"Extracted: {extracted.dict()}")
    
    # ─────────────────────────────────────────────
    # HANDLE CANCEL INTENT
    # ─────────────────────────────────────────────
    if extracted.intent_type == "cancel_leave":
        cancelled_state = LeaveState(
            intent_type="cancel_leave",
            parsing_status="cancelled",
            chat_response="Leave application cancelled. Feel free to start over whenever you'd like.",
            session_id=session_id,
            empCode=empCode,
            username=username,
            application_date=application_date
        )
        return cancelled_state.dict()

    # ─────────────────────────────────────────────
    # SET INTENT TYPE (apply_leave or update_leave)
    # ─────────────────────────────────────────────
    if extracted.intent_type:
        state.intent_type = extracted.intent_type
    elif not state.intent_type:
        # Default to apply_leave if not set
        state.intent_type = "apply_leave"
    
    # FALLBACK: If LLM missed confirmation, check manually
    if extracted.confirmation is None and state.parsing_status == "needs_confirmation":
        msg_lower = user_message.strip().lower()
        if msg_lower in ["yes", "yeah", "yep", "ok", "okay", "confirm", "correct", "sure"]:
            extracted.confirmation = "yes"
            logger.info("FALLBACK: Detected 'yes' confirmation manually")
        elif msg_lower in ["no", "nope", "nah", "change"]:
            extracted.confirmation = "no"
            logger.info("FALLBACK: Detected 'no' confirmation manually")

    # ─────────────────────────────────────────────
    # HANDLE CHANGE REQUESTS (change start/end/reason)
    # ─────────────────────────────────────────────
    if extracted.intent_to_change or extracted.intent_type == "update_leave":
        field = extracted.intent_to_change

        if field and field in {"start_date", "end_date", "reason"}:
            # If new value already provided in same message, apply directly
            if field == "start_date" and extracted.start_date:
                state.start_date = extracted.start_date
                state.awaiting_field = None
            elif field == "end_date" and extracted.start_date:
                state.end_date = extracted.start_date
                state.awaiting_field = None
            elif field == "reason" and extracted.reason:
                state.reason = extracted.reason
                state.awaiting_field = None

            else:
                setattr(state, field, None)
                state.awaiting_field = field
                state.chat_response = f"Please provide new {field.replace('_', ' ')}."
                state.parsing_status = "incomplete"
                state.intent_type = "update_leave"
                return state.dict()

        elif extracted.intent_type == "update_leave" and not field:
            # User said "update" but didn't specify what
            state.parsing_status = "incomplete"
            state.intent_type = "update_leave"
            state.chat_response = (
                "What would you like to change? "
                "You can say: change start date, change end date, or change reason."
            )
            return state.dict()

    # ─────────────────────────────────────────────
    # HANDLE CONFIRMATION STEP
    # ─────────────────────────────────────────────
    if state.parsing_status == "needs_confirmation" and not state.preview_confirmed:
        if extracted.confirmation == "yes":
            state.preview_confirmed = True
            state.parsing_status = "complete"
            state.message_for_user = (
                "Parsing has been completed. Checking genuineness score."
            )
            return state.dict()

        if extracted.confirmation == "no":
            state.parsing_status = "incomplete"
            state.intent_type = "update_leave"
            state.chat_response = "Okay, what would you like to change?"
            return state.dict()
        
        return state.dict()

    # ─────────────────────────────────────────────
    # DATE HANDLING 
    # ─────────────────────────────────────────────

    # CASE 1: Bot is waiting for a specific field
    if state.awaiting_field == "start_date" and extracted.start_date:
        state.start_date = extracted.start_date
        state.awaiting_field = None

    elif state.awaiting_field == "end_date" and extracted.start_date:
        # user usually gives ONE date → treat it as end_date
        state.end_date = extracted.start_date
        state.awaiting_field = None

    # CASE 2: Normal extraction (apply flow)
    else:
        if extracted.start_date:
            state.start_date = extracted.start_date
        if extracted.end_date:
            state.end_date = extracted.end_date

    # ─────────────────────────────────────────────
    # REASON & MEDICAL DOC
    # ─────────────────────────────────────────────
    if extracted.reason:
        state.reason = extracted.reason

    if extracted.medical_document is not None:
        state.medical_document = extracted.medical_document


    # ─────────────────────────────────────────────
    # DAY TYPE (FULL / HALF DAY)
    # ─────────────────────────────────────────────
    if extracted.daytype:
        state.daytype = extracted.daytype
    elif not state.daytype:
        state.daytype = "fullday"   # default

    # ─────────────────────────────────────────────
    # BUSINESS VALIDATION (duration, rules)
    # ─────────────────────────────────────────────
    state = validate_state(state)
    state.awaiting_field = None

    # ─────────────────────────────────────────────
    # PREVIEW BEFORE FINAL CONFIRMATION
    # ─────────────────────────────────────────────
    if state.parsing_status == "complete" and not state.preview_confirmed:
        state.parsing_status = "needs_confirmation"
        state.chat_response = (
            "Please confirm your leave:\n\n"
            f"Start Date: {state.start_date}\n"
            f"End Date: {state.end_date}\n"
            f"Day Type: {state.daytype}\n"
            f"Reason: {state.reason}\n\n"
            "Reply YES to confirm or tell me what to change."
        )

        return state.dict()

    # ─────────────────────────────────────────────
    # FINAL STATE
    # ─────────────────────────────────────────────
    logger.info(f"Final State={state.dict()}")
    return state.dict()



