from asyncio import Queue
from dataclasses import dataclass

from .choices import Priorities


@dataclass
class Settings:
    notification_service_host: str
    count_high: int
    count_middle: int
    count_low: int


@dataclass
class Queues:
    high: Queue
    middle: Queue
    low: Queue

    def get_queue_by_priority(self, priority: Priorities):
        mapping = {
            Priorities.high: self.high,
            Priorities.middle: self.middle,
            Priorities.low: self.low,
        }
        return mapping.get(priority)


@dataclass
class Data:
    msg: str
