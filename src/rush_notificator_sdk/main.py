import os
import asyncio
from typing import Tuple, List
from string import ascii_letters, digits
import logging

import aiohttp
from aiohttp.client_exceptions import ServerConnectionError

from .choices import Priorities, MessageType
from .dataclasses import Settings, Queues, Data


LETTERS_DIGITS = ascii_letters + digits
logger = logging.getLogger(__name__)


class RushNotificatorSDK:
    def __init__(self):
        self.settings = Settings(
            notification_service_host=os.getenv('RUSH_NOTIFICATION_HOST'),
            count_high=int(os.getenv('RUSH_NOTIFICATION_HIGH', 3)) or 1,
            count_middle=int(os.getenv('RUSH_NOTIFICATION_COUNT_MIDDLE', 2)) or 1,
            count_low=int(os.getenv('RUSH_NOTIFICATION_COUNT_LOW', 1)) or 1,
        )
        self.queues = Queues(
            high=asyncio.Queue(),
            middle=asyncio.Queue(),
            low=asyncio.Queue(),
        )
        self.__tasks = []
        for i in range(self.settings.count_high):
            self.__tasks.append(asyncio.create_task(self.__task(priority=Priorities.high, name=f'High priority #{i}')))
        for i in range(self.settings.count_middle):
            self.__tasks.append(asyncio.create_task(
                self.__task(priority=Priorities.middle, name=f'Middle priority #{i}')))
        for i in range(self.settings.count_low):
            self.__tasks.append(asyncio.create_task(self.__task(priority=Priorities.low, name=f'Low priority #{i}')))
        self.kwgs = {'ssl': False} if aiohttp.__version__ >= '3.8.0' else {'verify_ssl': False}

    async def __publish(self, aio_session: aiohttp.ClientSession, msg: str, msg_type: MessageType) -> Tuple[dict, int]:
        data = {
            "msg": msg,
            "msg_type": msg_type
        }

        out = {}
        async with aio_session.post(
                f'http://{self.settings.notification_service_host}/api/notifications/send/', json=data,
                **self.kwgs) as resp:
            if resp.status == 200:
                out = await resp.json()

        return out, resp.status

    async def __task(self, priority: Priorities, name):
        queue = self.queues.get_queue_by_priority(priority=priority)
        while True:
            async with aiohttp.ClientSession() as aio_session:
                data: Data = await queue.get()
                if not data:
                    logger.info(f'Task {name} done!')
                try:
                    resp, status = await self.__publish(aio_session=aio_session, msg=data.msg, msg_type=data.msg_type)
                    if status != 200:
                        logger.error(f"Problem send notification. Status {status}")
                except ServerConnectionError as e:
                    logger.exception(e)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.exception(e)

    async def publish_high(self, msg: str, msg_type: MessageType = MessageType.FEEDBACK):
        await self.queues.high.put(Data(msg=msg, msg_type=msg_type))

    async def publish_middle(self, msg: str, msg_type: MessageType = MessageType.FEEDBACK):
        await self.queues.middle.put(Data(msg=msg, msg_type=msg_type))

    async def publish_low(self, msg: str, msg_type: MessageType = MessageType.FEEDBACK):
        await self.queues.low.put(Data(msg=msg, msg_type=msg_type))

    async def publish_force(self, msg: str, msg_type: MessageType = MessageType.FEEDBACK):
        async with aiohttp.ClientSession() as aio_session:
            try:
                resp, status = await self.__publish(aio_session=aio_session, msg=msg, msg_type=msg_type)
            except ServerConnectionError as e:
                logger.exception(e)
                resp, status = {}, None
            return resp, status

    async def close(self):
        async def check_shutdown_tasks(tasks: List[asyncio.Task]):
            for task in tasks:
                if not task.done():
                    await asyncio.sleep(2)
                    await check_shutdown_tasks(tasks=[task])
            return

        for i in range(self.settings.count_high):
            await self.queues.high.put(None)
        for i in range(self.settings.count_middle):
            await self.queues.middle.put(None)
        for i in range(self.settings.count_low):
            await self.queues.low.put(None)

        await check_shutdown_tasks(tasks=self.__tasks)
