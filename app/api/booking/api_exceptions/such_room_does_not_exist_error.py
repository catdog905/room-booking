class SuchRoomDoesNotExistError(Exception):
    def __init__(self, room_id: str):
        self.room_id = room_id
