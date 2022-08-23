from enum import Enum


class Priorities(str, Enum):
    high = 'high'
    middle = 'middle'
    low = 'low'


class MessageType(str, Enum):
    FEEDBACK = 'FEEDBACK'
    ISSUE = 'ISSUE'
