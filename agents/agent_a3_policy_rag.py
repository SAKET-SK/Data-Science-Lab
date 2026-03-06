import os
from dotenv import load_dotenv
from docx import Document
import openai

load_dotenv()


# Set OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")
POLICY_DOC_PATH = os.getenv("POLICY_DOC_PATH")

POLICY_QUESTIONS = {

    "Family function": [
        {
            "key": "cl_allowed_for_family_function",
            "question": "Is Casual Leave allowed for family functions?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_family_function",
            "question": "Is Privilege Leave allowed for family functions?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "max_pl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Privilege Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "weekends_counted_for_leave",
            "question": "Are weekends and public holidays counted as part of the leave period when leave is taken?",
            "answer_type": "YES_NO"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed",
            "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        },
        {
        "key": "max_lwp_consecutive_days",
        "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
        "answer_type": "NUMBER"
    }

    ],

    "Going Outstation": [
        {
            "key": "cl_allowed_for_outstation",
            "question": "Is Casual Leave allowed for outstation travel?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_outstation",
            "question": "Is Privilege Leave allowed for outstation travel?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "max_pl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Privilege Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "monthly_leave_limit",
            "question": "What is the maximum number of leave days an associate can take in a month?",
            "answer_type": "NUMBER"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed",
            "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_lwp_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        }

    ],

    "Sickness for Self": [
        {
            "key": "cl_allowed_for_sickness",
            "question": "Is Casual Leave allowed for sickness or illness?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_sickness",
            "question": "Is Privilege Leave allowed for sickness or illness?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed_when_balances_exhausted",
            "question": "Is Leave Without Pay allowed when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_lwp_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Leave Without Pay as a special case?",
            "answer_type": "NUMBER"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
        "key": "lwp_allowed",
        "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
        "answer_type": "YES_NO"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        }

    ],

    "Sickness of family member": [
        {
            "key": "cl_allowed_for_family_sickness",
            "question": "Is Casual Leave allowed for sickness of a family member?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_family_sickness",
            "question": "Is Privilege Leave allowed for sickness of a family member?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "weekends_counted_for_leave",
            "question": "Are weekends and public holidays counted as part of the leave period?",
            "answer_type": "YES_NO"
        },
        {
            "key": "monthly_leave_limit",
            "question": "What is the maximum number of leave days allowed in a month?",
            "answer_type": "NUMBER"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
        "key": "lwp_allowed",
        "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
        "answer_type": "YES_NO"
        },
        {
            "key": "max_lwp_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        }

        ],

    "Death of Relatives": [
        {
            "key": "cl_allowed_for_death_of_relatives",
            "question": "Is Casual Leave allowed in case of death of relatives?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_death_of_relatives",
            "question": "Is Privilege Leave allowed in case of death of relatives?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "special_approval_required_for_long_leave",
            "question": "Is special approval required for leave exceeding eight consecutive days?",
            "answer_type": "YES_NO"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed",
            "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_lwp_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        }

    ],

    "Death of family member": [
        {
            "key": "special_leave_for_death_of_family_member",
            "question": "Is there any special leave provided in case of death of a family member?",
            "answer_type": "YES_NO"
        },
        {
            "key": "cl_allowed_for_death_of_family_member",
            "question": "Is Casual Leave allowed in case of death of a family member?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_death_of_family_member",
            "question": "Is Privilege Leave allowed in case of death of a family member?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_leave_days_with_approval",
            "question": "Is management approval required for leave exceeding eight consecutive days?",
            "answer_type": "YES_NO"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed",
            "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_lwp_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
            "answer_type": "NUMBER"
        }

    ],

    "Other": [
        {
            "key": "cl_allowed_for_other_reasons",
            "question": "Is Casual Leave allowed for personal or other unspecified reasons?",
            "answer_type": "YES_NO"
        },
        {
            "key": "pl_allowed_for_other_reasons",
            "question": "Is Privilege Leave allowed for personal or other unspecified reasons?",
            "answer_type": "YES_NO"
        },
        {
            "key": "max_cl_consecutive_days",
            "question": "What is the maximum consecutive number of days allowed for Casual Leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "monthly_leave_limit",
            "question": "What is the maximum number of leave days allowed per month?",
            "answer_type": "NUMBER"
        },
        {
            "key": "minimum_team_availability_percentage",
            "question": "What is the minimum percentage of team members required to be available when an employee applies for leave?",
            "answer_type": "NUMBER"
        },
        {
            "key": "lwp_allowed",
            "question": "Is Leave Without Pay allowed for employees when paid leave balances are exhausted?",
            "answer_type": "YES_NO"
        },
        {
            "key": "lwp_allowed_for_trainee",
            "question": "Is Leave Without Pay allowed for Trainee employees?",
            "answer_type": "YES_NO"
        },
        {
    "key": "max_lwp_consecutive_days",
    "question": "What is the maximum consecutive number of days allowed for Leave Without Pay?",
    "answer_type": "NUMBER"
}

    ]

}


# --------------LOAD POLICY --------------------


def load_policy_text():
    doc = Document(POLICY_DOC_PATH)
    full_text = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)
    
    return "\n".join(full_text)

policy_text = load_policy_text()


# --------- CHUNK POLICY---------------------

def chunk_text(text, max_words=800):
    words = text.split()
    return [
        " ".join(words[i:i + max_words])
        for i in range(0, len(words), max_words)
    ]


# ------------------PARSE ANSWER PARSER -----------------------

def parse_policy_value(value):
    if value is None:
        return None

    val = value.strip().lower()

    if val in ["yes", "y", "true"]:
        return True

    if val in ["no", "n", "false"]:
        return False

    if val.isdigit():
        return int(val)

    return None



# ----------------- LLM -------------------

SYSTEM_PROMPT = """
You are an HR policy assistant.

RULES:
- Answer ONLY using the provided policy document.
- If the answer is not explicitly mentioned, say "Not specified in policy".
- Answer strictly as YES, NO, or a NUMBER.
- Do not explain.
"""

def ask_policy_llm(policy_text, question, answer_type):

    chunks = chunk_text(policy_text)
    
    for chunk in chunks:
        user_prompt = f"""
POLICY DOCUMENT:
{chunk}

QUESTION:
{question}

Answer type: {answer_type}
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()

        # If model gives a concrete answer, return it
        if answer not in ["Not specified in policy", ""]:
            return answer

    # If no chunk contained the answer
    return "Not specified in policy"

def query_leave_policies(state: dict):
    reason = state["reason"]
    questions= POLICY_QUESTIONS.get(reason,[])

    policy_facts={}
    for q in questions:
        raw = ask_policy_llm(
            policy_text,
            q["question"],
            q["answer_type"]
        )
        policy_facts[q["key"]]=parse_policy_value(raw)

    return policy_facts

"""
state = {
    "emp_id": "OMI-0001",
    "reason": "Other",
    "start_date": "2026-01-08",
    "end_date": "2026-01-08",
    "duration": 1
}

policy_facts = query_leave_policies(state)
print(policy_facts)


"""
