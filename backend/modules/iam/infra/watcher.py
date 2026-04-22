from __future__ import annotations

import contextlib
import json
import os
import threading
import time
import uuid
from collections.abc import Callable

from redis import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError

from core.logger import get_logger

try:
    from casbin.persist.watcher import Watcher
except ImportError:

    class Watcher:  # pragma: no cover - compatibility shim
        def set_update_callback(self, func):
            pass

        def update(self):
            pass


logger = get_logger(__name__)


class RedisWatcher(Watcher):
    def __init__(self, client: Redis, prefix: str = "casbin_watcher"):
        self.client = client
        self.channel = f"{prefix}:policy_update"
        self.instance_id = uuid.uuid4().hex
        self.callback: Callable[[], None] | None = None
        self.pubsub = self.client.pubsub()
        self.thread: threading.Thread | None = None
        self.running = False

        self._start_listen()

    def set_update_callback(self, func: Callable[[], None]) -> None:
        self.callback = func

    def update(self) -> None:
        try:
            payload = {"type": "update", "source": self.instance_id}
            self.client.publish(self.channel, json.dumps(payload))
            logger.info(
                "Published policy update to {} pid={} instance={}",
                self.channel,
                os.getpid(),
                self.instance_id,
            )
        except Exception as exc:
            logger.error("Failed to publish policy update: {}", exc)

    def _start_listen(self) -> None:
        self.running = True
        try:
            self.pubsub.subscribe(self.channel)
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            logger.info("Started RedisWatcher on channel {}", self.channel)
        except Exception as exc:
            logger.error("Failed to start RedisWatcher: {}", exc)

    def _listen(self) -> None:
        while self.running:
            try:
                for message in self.pubsub.listen():
                    if not self.running:
                        break
                    if message["type"] != "message":
                        continue
                    raw = message.get("data")
                    source = None
                    try:
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", errors="ignore")
                        data = json.loads(raw) if isinstance(raw, str) else {}
                        source = data.get("source")
                    except Exception:
                        source = None
                    if source == self.instance_id:
                        continue
                    logger.info(
                        "Received update message from {} pid={} instance={} source={}",
                        self.channel,
                        os.getpid(),
                        self.instance_id,
                        source or "-",
                    )
                    if self.callback:
                        self.callback()
            except RedisTimeoutError:
                continue
            except Exception as exc:
                if not self.running:
                    break
                logger.error("Error in RedisWatcher listener: {}", exc)
                time.sleep(1)
                with contextlib.suppress(Exception):
                    self.pubsub.close()

                self.pubsub = self.client.pubsub()
                self.pubsub.subscribe(self.channel)

    def close(self) -> None:
        self.running = False
        if self.pubsub:
            try:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            except Exception:
                pass
