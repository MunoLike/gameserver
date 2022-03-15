
import time

from sqlalchemy import text

from .db import engine


class TimeLimitter():
    def __init__(self, room_id: int):
        self.wait_time: int = 300
        self.room_id: int = room_id

    def __call__(self):
        time.sleep(self.wait_time)
        print("auto-deleted")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    delete from `room` where `room_id` = :room_id
                    """
                ),
                {"room_id": self.room_id}
            )

            conn.execute(
                text(
                    """
                    delete from `room_user` where `room_id` = :room_id
                    """
                ),
                {"room_id": self.room_id}
            )
