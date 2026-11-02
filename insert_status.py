from enum import Enum 
class InsertStatus(Enum):
    INSERTED = 1 
    TOO_LARGE = 2
    FAIL = 3