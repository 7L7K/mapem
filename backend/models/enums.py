# backend/models/enums.py
from enum import Enum

class GenderEnum(str, Enum):
    male   = "male"
    female = "female"
    other  = "other"
    unknown = "unknown"

class EventTypeEnum(str, Enum):
    birth      = "birth"
    death      = "death"
    marriage   = "marriage"
    residence  = "residence"
    immigration = "immigration"
    emigration  = "emigration"
    census      = "census"
    other       = "other"

class LocationStatusEnum(str, Enum):
    valid          = "valid"
    vague_state    = "vague_state_pre1890"
    unresolved     = "unresolved"
    historical     = "historical"
    duplicate      = "duplicate"
    manual_override= "manual_override"      
    ok             ="ok"

class SourceTypeEnum(str, Enum):
    gedcom   = "gedcom"
    census   = "census"
    manual   = "manual"
    api      = "api"
    unknown  = "unknown"

class FamilyTypeEnum(str, Enum):
    nuclear  = "nuclear"
    extended = "extended"
    single   = "single_parent"
    other    = "other"

class ActionTypeEnum(str, Enum):
    upload      = "upload"
    edit        = "edit"
    delete      = "delete"
    merge       = "merge"
    manual_fix  = "manual_fix"
