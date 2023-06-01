import asyncio
from collections import defaultdict
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Dict, Optional

import pydantic
from pydantic import AmqpDsn
from pydantic.dataclasses import dataclass

from great_expectations import get_context
from great_expectations.agent.actions.agent_action import ActionResult
from great_expectations.agent.event_handler import (
    EventHandler,
)
from great_expectations.agent.message_service.asyncio_rabbit_mq_client import (
    AsyncRabbitMQClient,
    ClientError,
)
from great_expectations.agent.message_service.subscriber import (
    EventContext,
    OnMessageCallback,
    Subscriber,
    SubscriberError,
)
from great_expectations.agent.models import UnknownEvent
from great_expectations.core.http import create_session

if TYPE_CHECKING:
    from great_expectations.data_context import CloudDataContext

HandlerMap = Dict[str, OnMessageCallback]


@dataclass(frozen=True)
class GXAgentConfig:
    """GXAgent configuration.
    Attributes:
        queue: name of queue
        connection_string: address of broker service
    """

    queue: str
    connection_string: AmqpDsn


class GXAgent:
    """
    Run GX in any environment from GX Cloud.

    To start the agent, install Python and great_expectations and run `gx-agent`.
    The agent loads a DataContext configuration from GX Cloud, and listens for
    user events triggered from the UI.
    """

    def __init__(self):
        print("Initializing GX-Agent")
        self._config = self._get_config()
        print("Loading a DataContext - this might take a moment.")
        self._context: CloudDataContext = get_context(cloud_mode=True)
        print("DataContext is ready.")

        # Create a thread pool with a single worker, so we can run long-lived
        # GX processes and maintain our connection to the broker. Note that
        # the CloudDataContext cached here is used by the worker, so
        # it isn't safe to increase the number of workers running GX jobs.
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._current_task: Optional[Future] = None
        self._correlation_ids = defaultdict(lambda: 0)

    def run(self) -> None:
        """Open a connection to GX Cloud."""

        print("Opening connection to GX Cloud")
        self._listen()
        print("Connection to GX Cloud has been closed.")

    def _listen(self) -> None:
        """Manage connection lifecycle."""
        subscriber = None
        try:
            client = AsyncRabbitMQClient(url=self._config.connection_string)
            subscriber = Subscriber(client=client)
            print("GX-Agent is ready.")
            # Open a connection until encountering a shutdown event
            subscriber.consume(
                # TODO: replace with queue from agent-sessions endpoint
                queue=self._config.queue,
                on_message=self._handle_event_as_thread_enter,
            )
        except KeyboardInterrupt:
            print("Received request to shutdown.")
        except (SubscriberError, ClientError):
            print("Connection to GX Cloud has encountered an error.")
        finally:
            if subscriber is not None:
                subscriber.close()

    def _handle_event_as_thread_enter(self, event_context: EventContext) -> None:
        """Schedule _handle_event to run in a thread.

        Callback passed to Subscriber.consume which forwards events to
        the EventHandler for processing.

        Args:
            event_context: An Event with related properties and actions.
        """
        if self._reject_correlation_id(event_context.correlation_id) is True:
            # this event has been redelivered too many times - remove it from circulation
            event_context.processed_with_failures()
            return
        elif self._can_accept_new_task() is not True or isinstance(
            event_context.event, UnknownEvent
        ):
            # request that this message is redelivered later. If the event is UnknownEvent
            # we don't understand it, so requeue it in the hope that someone else does.
            loop = asyncio.get_event_loop()
            loop.create_task(event_context.redeliver_message())
            return

        # send this message to a thread for processing
        self._current_task = self._executor.submit(
            self._handle_event, event_context=event_context
        )
        # TODO lakitu-139: record job as started

        if self._current_task is not None:
            # add a callback for when the thread exits and pass it the event context
            on_exit_callback = partial(
                self._handle_event_as_thread_exit, event_context=event_context
            )
            self._current_task.add_done_callback(on_exit_callback)

    def _handle_event(self, event_context: EventContext) -> ActionResult:
        """Pass events to EventHandler.

        Callback passed to Subscriber.consume which forwards events to
        the EventHandler for processing.

        Args:
            event_context: event with related properties and actions.
        """
        # warning:  this method will not be executed in the main thread

        print(
            f"Starting job {event_context.event.type} ({event_context.correlation_id}) "
        )
        handler = EventHandler(context=self._context)
        # This method might raise an exception. Allow it and handle in _handle_event_as_thread_exit
        result = handler.handle_event(
            event=event_context.event, id=event_context.correlation_id
        )
        return result

    def _handle_event_as_thread_exit(
        self, future: Future, event_context: EventContext
    ) -> None:
        """Callback invoked when the thread running GX exits.

        Args:
            future: object returned from the thread
            event_context: event with related properties and actions.
        """
        # warning:  this method will not be executed in the main thread

        # get results or errors from the thread
        error = future.exception()
        # todo: underscore to appease linter - rename to `result` once this is used
        _result = None
        if error is None:
            _result = future.result()
            print(
                f"Completed job {event_context.event.type} ({event_context.correlation_id})"
            )
        else:
            print(error)
            print(
                f"Failed to complete job {event_context.event.type} ({event_context.correlation_id})"
            )

        # TODO lakitu-139: record job as complete and send results

        # ack message and cleanup resources
        event_context.processed_successfully()
        self._current_task = None

    def _can_accept_new_task(self) -> bool:
        """Are we currently processing a task, or are we free to take a new one?"""
        return self._current_task is None or self._current_task.done()

    def _reject_correlation_id(self, id: str):
        """Has this correlation ID been seen too many times?"""
        MAX_REDELIVERY = 10
        MAX_KEYS = 100000
        self._correlation_ids[id] += 1
        delivery_count = self._correlation_ids[id]
        if delivery_count > MAX_REDELIVERY:
            should_reject = True
        else:
            should_reject = False
        # ensure the correlation ids dict doesn't get too large:
        if len(self._correlation_ids.keys()) > MAX_KEYS:
            self._correlation_ids.clear()
        return should_reject

    @classmethod
    def _get_config(cls) -> GXAgentConfig:
        """Construct GXAgentConfig."""

        # ensure we have all required env variables, and provide a useful error if not

        class GxAgentConfigSettings(pydantic.BaseSettings):
            gx_cloud_base_url: str = "https://api.greatexpectations.io"
            gx_cloud_organization_id: str
            gx_cloud_access_token: str

        config = GxAgentConfigSettings()

        # obtain the broker url and queue name from Cloud

        agent_sessions_url = f"{config.gx_cloud_base_url}/organizations/{config.gx_cloud_organization_id}/agent-sessions"

        session = create_session(access_token=config.gx_cloud_access_token)

        response = session.post(agent_sessions_url)
        if response.ok is not True:
            raise GXAgentError("Unable to connect to Cloud")

        json_response = response.json()
        queue = json_response["queue"]
        connection_string = json_response["connection_string"]

        try:
            # pydantic will coerce the url to the correct type
            return GXAgentConfig(queue=queue, connection_string=connection_string)
        except pydantic.ValidationError as validation_err:
            raise GXAgentError(
                f"Missing or badly formed environment variable\n{validation_err.errors()}"
            ) from validation_err


class GXAgentError(Exception):
    ...
