"""
Conversation memory for multi-turn chats.

Two kinds of memory are kept per user:
  * dialogue state : the bot asked a question and is waiting for the answer
                     (e.g. "which dates?" or "confirm this leave? yes/no")
  * last context   : the last read-only question, so a follow-up such as
                     "what about employee 2?" can reuse it

Memory is held in the server's RAM with a time limit. That is fine for a
single-server demo; a production system would keep it in Redis or the database.
"""

import re
import time

from app.models.employee import Employee
from app.nlp.date_parser import extract_dates
from app.nlp.intent_classifier import extract_entities
from app.handlers.common import (make_reply, find_customer_in_query,
                                 find_supplier_in_query, find_item_in_query)

STATE_TTL = 300      # seconds an open question stays valid
CONTEXT_TTL = 600    # seconds a follow-up can refer back to the last question

# Intents that change data are never repeated as follow-ups
WRITE_INTENTS = {"apply_leave", "decide_leave"}

_state = {}
_context = {}

YES = re.compile(r"^\s*(yes|y|yeah|yep|yup|sure|ok|okay|confirm|confirmed|go ahead|do it)\b[\s.!]*$", re.I)
NO = re.compile(r"^\s*(no|n|nope|no thanks|cancel|stop|never\s?mind|abort)\b[\s.!]*$", re.I)

FOLLOWUP = re.compile(
    r"^\s*(?:and\s+)?(?:what|how)\s+about\s+(.+?)\s*\??\s*$"
    r"|^\s*and\s+(?:for\s+)?(\S+(?:\s+\S+){0,3}?)\s*\??\s*$", re.I)


# ---------------------------------------------------------------- state
def set_state(user_id, kind, data):
    _state[str(user_id)] = {"kind": kind, "data": data, "ts": time.time()}


def get_state(user_id):
    s = _state.get(str(user_id))
    if s and time.time() - s["ts"] > STATE_TTL:
        _state.pop(str(user_id), None)
        return None
    return s


def clear_state(user_id):
    _state.pop(str(user_id), None)


def remember(user_id, intent, entities):
    if intent in WRITE_INTENTS:
        return
    _context[str(user_id)] = {"intent": intent, "entities": dict(entities), "ts": time.time()}


def recall(user_id):
    c = _context.get(str(user_id))
    if c and time.time() - c["ts"] > CONTEXT_TTL:
        _context.pop(str(user_id), None)
        return None
    return c


# ---------------------------------------------------------------- open questions
def continue_dialogue(user_id, query):
    """If the bot is waiting for an answer, handle it. Returns a reply or None."""
    state = get_state(user_id)
    if not state:
        return None

    from app.handlers import hr   # imported here to avoid a circular import

    kind, data = state["kind"], state["data"]

    if NO.match(query):
        clear_state(user_id)
        return make_reply("Okay, I've cancelled that.")

    if kind == "leave_dates":
        dates = extract_dates(query)
        if dates:
            clear_state(user_id)
            emp = Employee.query.get(data["employee_id"])
            return hr.plan_leave(emp, dates, user_id)

    elif kind == "leave_confirm":
        if YES.match(query):
            clear_state(user_id)
            return hr.commit_leave(data)

    clear_state(user_id)    # anything else means the user moved on
    return None


# ---------------------------------------------------------------- follow-ups
def detect_followup(user_id, query):
    """
    "what about employee 2?" / "and for acme" -> (intent, entities, text)
    re-using the previous question. Returns None if it is not a follow-up.
    """
    m = FOLLOWUP.match(query)
    ctx = recall(user_id)
    if not m or not ctx:
        return None

    text = m.group(1) or m.group(2)
    new_entities = extract_entities(text)
    about_me = re.search(r"\b(me|my|myself|mine)\b", text, re.I) is not None
    names_something = bool(find_customer_in_query(text) or find_supplier_in_query(text)
                           or find_item_in_query(text))

    if not (new_entities or about_me or names_something):
        return None

    entities = dict(ctx["entities"])
    entities.update(new_entities)
    if about_me:
        entities.pop("employee_id", None)
    return ctx["intent"], entities, text

def clear_user(user_id):
    """Forget everything about this user's conversation (called on login)."""
    _state.pop(str(user_id), None)
    _context.pop(str(user_id), None)