from dataclasses import dataclass
import csv
from os import path
import os.path


@dataclass
class Room:
    # Unneeded types are omitted: id, room type
    name_original: str
    name_en: str
    name_ru: str
    email: str
    schedule_link: str


class Rooms:
    _email = str

    _rooms: dict[_email, Room]

    def __init__(self) -> None:
        self._rooms = {}

    def insert(self, room: Room):
        self._rooms[room.email] = room

    def get_by_email(self, email: _email) -> Room | None:
        return self._rooms.get(email)

    def get_by_name(self, name: str) -> Room | None:
        for room in self._rooms.values():
            if any(
                room_name == name
                for room_name in (room.name_original, room.name_en, room.name_ru)
            ):
                return room

        return None


def _bookable_rooms() -> Rooms:
    rooms = Rooms()

    # TODO(metafates): is it how it's suppossed to be done?
    csv_path = path.join(path.dirname(__file__), "bookable_rooms.csv")
    with open(csv_path) as file:
        for row in csv.DictReader(file):
            # TODO(metafates): make row parsing better
            room = Room(
                email=row["email"],
                name_original=row["name_original"],
                name_en=row["name_en"],
                name_ru=row["name_ru"],
                schedule_link=row["schedule_link"],
            )

            rooms.insert(room)

    return rooms


ROOMS = _bookable_rooms()
