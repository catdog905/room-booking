class SuchRoomDoesNotExistError(Exception):
    def __init__(self, room_id: str):
        self.room_id = room_id

    def __str__(self):
        return f"Room with id=\"{self.room_id}\" does not exist"
