from collections import defaultdict
from datetime import datetime
from typing import List, Dict

import aioredis
from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from accounts.models import User
from chat.dependencies.messages import get_request_user
from chat.permissions.chat_rooms import UserChatRoomMessagingPermissionsService
from chat.services import messages as messages_services
from core.config import settings
from mixins import dependencies as mixins_dependencies, permissions as mixins_permissions

router = APIRouter()


class WebSocketConnection:
    def __init__(self, websocket: WebSocket, user: User, chat_room_id: int, connected_at: datetime = datetime.now()):
        self.websocket = websocket
        self.user = user
        self.chat_room_id = chat_room_id
        self.connected_at = connected_at


class ChatRoomsWebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocketConnection]] = defaultdict(list)

    async def connect(self, websocket_connection: WebSocketConnection):
        await websocket_connection.websocket.accept()
        self.active_connections[websocket_connection.chat_room_id].append(websocket_connection)

    async def disconnect(self, websocket_connection: WebSocketConnection):
        await websocket_connection.websocket.close()
        chat_room_connections: List[WebSocketConnection] = self.active_connections[websocket_connection.chat_room_id]
        if websocket_connection in chat_room_connections:
            chat_room_connections.remove(websocket_connection)

    async def send_personal_message(self, websocket_connection: WebSocketConnection, message: dict):
        await websocket_connection.websocket.send_json(message)

    async def broadcast(self, message: dict, chat_room_id: int):
        for connection in self.active_connections[chat_room_id]:
            await self.send_personal_message(connection, message)


chat_rooms_websocket_manager = ChatRoomsWebSocketConnectionManager()
active_users_in_chat_rooms_redis_db = aioredis.from_url(settings.ACTIVE_USERS_IN_CHAT_ROOMS_REDIS_DB_URL)


@router.websocket('/chat_rooms/{chat_room_id}/messages')
async def messages_websocket_endpoint(
        chat_room_id: int,
        websocket: WebSocket,
        request_user: User = Depends(get_request_user),
        db_session: Session = Depends(mixins_dependencies.db_session)
):
    permissions: mixins_permissions.PermissionsServiceABC = UserChatRoomMessagingPermissionsService(
        request_user, chat_room_id, db_session
    )
    if not await permissions.check_permissions():
        return await websocket.close()
    websocket_connection = WebSocketConnection(websocket, request_user, chat_room_id)
    await chat_rooms_websocket_manager.connect(websocket_connection)
    try:
        while True:
            # look for receiving bytes as well (https://stackoverflow.com/a/42246632/13394740 may help)
            message_text = await websocket.receive_text()
            if not await permissions.check_permissions():
                return await chat_rooms_websocket_manager.disconnect(websocket_connection)
            new_message = await messages_services.MessagesCreatingService(db_session).create_message(
                chat_room_id, message_text, request_user.id
            )
            await chat_rooms_websocket_manager.broadcast(
                {
                    'user': request_user.id,
                    'message': new_message.text,
                },
                chat_room_id
            )
    except WebSocketDisconnect:
        await chat_rooms_websocket_manager.disconnect(websocket_connection)
        await chat_rooms_websocket_manager.broadcast({'Client': 'has left the chat'}, chat_room_id)
