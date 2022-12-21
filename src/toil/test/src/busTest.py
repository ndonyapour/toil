# Copyright (C) 2015-2022 Regents of the University of California
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

import logging

from threading import Thread, current_thread

from toil.bus import MessageBus, JobIssuedMessage
from toil.test import ToilTest

logger = logging.getLogger(__name__)

class MessageBusTest(ToilTest):
    def test_cross_thread_messaging(self):

        main_thread = current_thread()

        bus = MessageBus()

        message_count = 0

        # We will count the messages going to the handler
        def handler(received: JobIssuedMessage) -> None:
            """
            Handle a message in the main thread.
            """
            # Message should always arrive in the main thread.
            nonlocal message_count
            logger.debug("Got message: %s", received)
            self.assertEqual(current_thread(), main_thread)
            message_count += 1

        bus.subscribe(JobIssuedMessage, handler)

        # And we will collect them in an inbox
        box = bus.connect([JobIssuedMessage])

        bus.publish(JobIssuedMessage("FromMainThread", "", 0))

        def send_thread_message() -> None:
            """
            Publish a message from some other thread.
            """
            bus.publish(JobIssuedMessage("FromOtherThread", "", 1))

        other_threads = []
        for _ in range(10):
            # Make a bunch of threads to send messages
            other_threads.append(Thread(target=send_thread_message))
        for t in other_threads:
            # Start all the threads
            t.start()
        for t in other_threads:
            # Wait for them to finish
            t.join()

        # We should ge tone message per thread, plus our own
        self.assertEqual(box.count(JobIssuedMessage), 11)
        # And having polled for those, our handler should have run
        self.assertEqual(message_count, 11)


