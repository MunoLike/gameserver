import json
import uuid
from enum import Enum
from sys import int_info
from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from this import d

from .db import engine


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    class Config:
        orm_mode = True


def create_user(name: str, leader_card_id: int) -> str:
    """Create new user and returns their token"""
    token = str(uuid.uuid4())
    # NOTE: tokenが衝突したらリトライする必要がある.
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `user` (name, token, leader_card_id) VALUES (:name, :token, :leader_card_id)"
            ),
            {"name": name, "token": token, "leader_card_id": leader_card_id},
        )
        # print(result)
    return token


def _get_user_by_token(conn, token: str) -> Optional[SafeUser]:
    result = conn.execute(
        text("select * from `user` where `token`=:token"), dict(token=token)
    )
    try:
        row = result.one()
    except NoResultFound:
        return None
    return SafeUser.from_orm(row)


def get_user_by_token(token: str) -> Optional[SafeUser]:
    with engine.begin() as conn:
        return _get_user_by_token(conn, token)


def _update_user(conn, token, name, leader_card_id) -> None:
    conn.execute(
        text(
            "\
        update `user`\
        set `name`=:name, `leader_card_id`=:leader_card_id\
        where token=:token\
        "
        ),
        dict(name=name, leader_card_id=leader_card_id, token=token),
    )


def update_user(token: str, name: str, leader_card_id: int) -> None:
    with engine.begin() as conn:
        _update_user(conn, token, name, leader_card_id)


# RoomAPIs


class LiveDifficulty(Enum):
    normal = 1
    hard = 2


def create_room(
    live_id: int, select_difficulty: LiveDifficulty, user: SafeUser
) -> Optional[int]:
    token = str(uuid.uuid4())
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `room` (live_id, host_id, joined_user_count, token) VALUES (:live_id, :host_id, 0, :token)"
            ),
            {"live_id": live_id, "host_id": user.id, "token": token},
        )

    with engine.begin() as conn:
        result = conn.execute(
            text("select `room_id` from `room` where `token`=:token"), {"token": token}
        )

        row = result.one()

    print(join_room(row.room_id, select_difficulty, user))

    return row.room_id


class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int

    class Config:
        orm_mode = True


def list_room(live_id: int) -> Optional[list[RoomInfo]]:
    room_info_list: list[RoomInfo] = []
    search_query = ""
    with engine.begin() as conn:
        if live_id == 0:
            search_query = "select * from `room`"
        else:
            search_query = "select * from `room` where `live_id`=:live_id"

        result = conn.execute(text(search_query), {"live_id": live_id})
        rooms = result.all()

        for room in rooms:
            room_info_list.append(RoomInfo.from_orm(room))

    return room_info_list


class JoinRoomResult(Enum):
    Ok = (1,)
    RoomFull = (2,)
    Disbanded = (3,)
    OtherError = 4


def _join_room(
    conn, room_id: int, select_difficulty: LiveDifficulty, user: SafeUser
) -> JoinRoomResult:

    result = conn.execute(
        text("select * from `room` where `room_id`=:room_id"), {"room_id": room_id}
    )

    try:
        room = result.one()
    except NoResultFound:
        return JoinRoomResult.Disbanded
    if room.joined_user_count == room.max_user_count:
        return JoinRoomResult.RoomFull

    result = conn.execute(
        text(
            "\
            update `room` \
            set `joined_user_count`=:updated_user_count \
            where `room_id`=:room_id\
            "
        ),
        {"updated_user_count": room.joined_user_count + 1, "room_id": room_id},
    )

    result = conn.execute(
        text(
            "\
            insert into `room_user` (`room_id`, `user_id`, `name`, `leader_card_id`, `select_difficulty`)\
            values (:room_id, :user_id, :name, :leader_card_id, :select_difficulty)\
            "
        ),
        {
            "room_id": room_id,
            "user_id": user.id,
            "name": user.name,
            "leader_card_id": user.leader_card_id,
            "select_difficulty": select_difficulty.value,
        },
    )

    return JoinRoomResult.Ok


def join_room(
    room_id: int, select_difficulty: LiveDifficulty, user: SafeUser
) -> JoinRoomResult:
    with engine.begin() as conn:
        try:
            return _join_room(conn, room_id, select_difficulty, user)
        except Exception as e:
            print(e)
            return JoinRoomResult.OtherError


class WaitRoomStatus(Enum):
    Waiting = 1
    LiveStart = 2
    Dissolution = 3


class RoomUser(BaseModel):
    user_id: int
    name: str
    leader_card_id: int
    select_difficulty: LiveDifficulty
    is_me: Optional[bool]
    is_host: Optional[bool]

    class Config:
        orm_mode = True


def wait_room(room_id: int, user: SafeUser) -> tuple[WaitRoomStatus, list[RoomUser]]:
    members_list: list[RoomUser] = []
    with engine.begin() as conn:
        result = conn.execute(
            text("select * from `room` where `room_id`=:room_id"), {"room_id": room_id}
        )

        try:
            room = result.one()
        except NoResultFound:
            return (WaitRoomStatus.Dissolution, None)

    with engine.begin() as conn:
        result = conn.execute(
            text("select * from `room_user` where `room_id`=:room_id"),
            {"room_id": room_id},
        )

        members = result.all()

        for i, member in enumerate(members):
            members_list.append(RoomUser.from_orm(member))
            members_list[i].is_me = members_list[i].user_id == user.id
            members_list[i].is_host = members_list[i].user_id == room.host_id

    return (WaitRoomStatus(room.wait_status), members_list)


def start_room(room_id: int):
    with engine.begin() as conn:
        conn.execute(
            text("update `room` set `wait_status` = 2 where `room_id` = :room_id"),
            {"room_id": room_id},
        )


def end_room(room_id: int, judge_count_list: list[int], score: int, user: SafeUser):
    print(room_id, judge_count_list, score, user)
    with engine.begin() as conn:
        conn.execute(
            text(
                "\
                    update `room_user` \
                    set `judge_count_list` = :judge_count_list, `score` = :score \
                    where `user_id` = :user_id and `room_id` = :room_id \
                "
            ),
            {
                "judge_count_list": json.dumps(judge_count_list),
                "score": score,
                "user_id": user.id,
                "room_id": room_id,
            },
        )


class ResultUser(BaseModel):
    user_id: int
    judge_count_list: list
    score: int


def result_room(room_id: int) -> list[ResultUser]:
    results: list[ResultUser] = []
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "select `user_id`, `judge_count_list`, `score` from `room_user` where `room_id` = :room_id"
            ),
            {"room_id": room_id},
        )

        members = result.all()

        for member in members:
            if member.score == -1:
                return []

            r = ResultUser(
                user_id=member.user_id,
                judge_count_list=json.loads(member.judge_count_list),
                score=member.score,
            )
            results.append(r)

    return results


def leave_room(room_id: int, user: SafeUser):
    with engine.begin() as conn:
        conn.execute(
            text(
                "\
                    delete from `room_user` \
                    where `user_id` = :user_id \
                "
            ),
            {"user_id": user.id},
        )

    with engine.begin() as conn:
        result = conn.execute(
            text("select `joined_user_count` from `room` where `room_id` = :room_id"),
            {"room_id": room_id},
        )

        room = result.one()

        conn.execute(
            text(
                "update `room` set `joined_user_count`=:count where `room_id` = :room_id"
            ),
            {"room_id": room_id, "count": room.joined_user_count - 1},
        )
