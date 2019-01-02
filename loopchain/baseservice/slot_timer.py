# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""loopchain timer service."""
from loopchain.baseservice import TimerService, Timer
import loopchain.utils as util


class SlotTimer:
    """Slot Timer"""

    def __init__(self, timer_key, duration, timer_service: TimerService, callback):
        self.__slot = 0
        self.__delayed = True
        self.__timer_key = timer_key
        self.__timer_service = timer_service
        self.__callback = callback

        timer_service.add_timer(
            timer_key,
            Timer(
                target=timer_key,
                duration=duration,
                is_repeat=True,
                is_run_at_start=True,
                callback=self.__timer_callback
            )
        )

    def __timer_callback(self):
        util.logger.spam(f"__timer_callback slot({self.__slot}) delayed({self.__delayed})")
        self.__slot += 1
        if self.__delayed:
            self.__delayed = False
            self.__call()
        elif self.__slot > 10:
            util.logger.warning(f"consensus timer loop broken slot({self.__slot}) delayed({self.__delayed})")
            # self.__call()

    async def __dispatch_callback(self):
        await self.__callback()
        self.__call()

    def __call(self):
        util.logger.spam(f"__call slot({self.__slot}) delayed({self.__delayed})")
        if self.__slot > 0:
            self.__slot -= 1
            self.__timer_service.get_event_loop().create_task(self.__dispatch_callback())
        else:
            self.__delayed = True

    def stop(self):
        if self.__timer_key in self.__timer_service.timer_list:
            self.__timer_service.stop_timer(self.__timer_key)
        self.__slot = 0
        self.__delayed = False
