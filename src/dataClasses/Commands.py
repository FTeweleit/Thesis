from enum import Enum


# ToDo: auch das könnte bessere Namen bekommen
class RmtCmd(bytes, Enum):
    StartTest = bytes.fromhex('00')
    StopTest = bytes.fromhex('01')
    Working = bytes.fromhex('02')
    NotWorking = bytes.fromhex('03')