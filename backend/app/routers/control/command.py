from enum import Enum
import uuid

from sqlmodel import Field, SQLModel


class DeviceCommand(Enum):
    NOOP = "noop"
    ADOPT = "adopt"
    PROVISION = "provision"
    REBOOT = "reboot"
    FORGET = "forget"
    UPDATE_INFORM = "update-inform"
    LOCATE = "locate"
    STOP_LOCATE = "stop-locate"


class Command(SQLModel, table=True):
    device_id: uuid.UUID = Field(primary_key=True)
    command: DeviceCommand = Field()
