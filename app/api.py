from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .time_limitter import TimeLimitter

from . import model
from .model import (
    JoinRoomResult,
    LiveDifficulty,
    ResultUser,
    RoomInfo,
    RoomUser,
    SafeUser,
    WaitRoomStatus,
)

app = FastAPI()

# Sample APIs


@app.get("/")
async def root():
    return {"message": "Hello World"}


# User APIs


class UserCreateRequest(BaseModel):
    user_name: str
    leader_card_id: int


class UserCreateResponse(BaseModel):
    user_token: str


@app.post("/user/create", response_model=UserCreateResponse)
def user_create(req: UserCreateRequest):
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


bearer = HTTPBearer()


def get_auth_token(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    assert cred is not None
    if not cred.credentials:
        raise HTTPException(status_code=401, detail="invalid credential")
    return cred.credentials


def _user_me(token: str):
    user = model.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=404)
    # print(f"user_me({token=}, {user=})")
    return user


@app.get("/user/me", response_model=SafeUser)
def user_me(token: str = Depends(get_auth_token)):
    return _user_me(token)


class Empty(BaseModel):
    pass


@app.post("/user/update", response_model=Empty)
def update(req: UserCreateRequest, token: str = Depends(get_auth_token)):
    """Update user attributes"""
    # print(req)
    model.update_user(token, req.user_name, req.leader_card_id)
    return {}


# RoomAPIs


class RoomCreateResponse(BaseModel):
    room_id: int


class RoomCreateRequest(BaseModel):
    live_id: int
    select_difficulty: LiveDifficulty


@app.post("/room/create", response_model=RoomCreateResponse)
def room_create(req: RoomCreateRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    room_id = model.create_room(req.live_id, req.select_difficulty, user)
    return RoomCreateResponse(room_id=room_id)


class RoomListResponse(BaseModel):
    room_info_list: list[RoomInfo]


class RoomListRequest(BaseModel):
    live_id: int


@app.post("/room/list", response_model=RoomListResponse)
def room_list(req: RoomListRequest):
    room_info_list = model.list_room(req.live_id)
    return RoomListResponse(room_info_list=room_info_list)


class RoomJoinResponse(BaseModel):
    join_room_result: JoinRoomResult


class RoomJoinRequest(BaseModel):
    room_id: int
    select_difficulty: LiveDifficulty


@app.post("/room/join", response_model=RoomJoinResponse)
def room_join(req: RoomJoinRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    join_room_result = model.join_room(req.room_id, req.select_difficulty, user)
    return RoomJoinResponse(join_room_result=join_room_result)


class RoomWaitResponse(BaseModel):
    status: WaitRoomStatus
    room_user_list: list[RoomUser]


class RoomWaitRequest(BaseModel):
    room_id: int


@app.post("/room/wait", response_model=RoomWaitResponse)
def room_wait(req: RoomWaitRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    status, room_user_list = model.wait_room(req.room_id, user)
    if not room_user_list:
        room_user_list = []
    return RoomWaitResponse(status=status, room_user_list=room_user_list)


class RoomStartRequest(BaseModel):
    room_id: int


@app.post("/room/start")
def room_start(req: RoomStartRequest, bg_tasks: BackgroundTasks):
    model.start_room(req.room_id)
    bg_tasks.add_task(TimeLimitter(req.room_id))
    return {}


class RoomEndRequest(BaseModel):
    room_id: int
    judge_count_list: list[int]
    score: int


@app.post("/room/end")
def room_end(req: RoomEndRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    model.end_room(req.room_id, req.judge_count_list, req.score, user)
    return {}


class RoomResultResponse(BaseModel):
    result_user_list: list[ResultUser]


class RoomResultRequest(BaseModel):
    room_id: int


@app.post("/room/result", response_model=RoomResultResponse)
def room_result(req: RoomResultRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    result_user_list = model.result_room(req.room_id, user)
    return RoomResultResponse(result_user_list=result_user_list)


class RoomLeaveRequest(BaseModel):
    room_id: int


@app.post("/room/leave")
def room_leave(req: RoomLeaveRequest, token: str = Depends(get_auth_token)):
    user = _user_me(token)
    model.leave_room(req.room_id, user)
    return {}
