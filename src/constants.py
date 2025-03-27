from enum import Enum
from typing import Dict, Any

class EntityType(Enum):
    PERSON_MALE = "male"
    PERSON_FEMALE = "female" 
    WORK = "work"
    FOOD = "food"

    def __str__(self):
        return self.value
    

asset_map = {
    EntityType.PERSON_MALE: {
        "name": "male", 
        "path": "assets/male.png",
        "eat": "assets/male_hungry.png",
        "mate": "assets/male_love.png",
        "dead": "assets/male_dead.png",
        "work": "assets/male_broke.png",
        "rest": "assets/male_rest.png"
        },
    EntityType.PERSON_FEMALE: {
        "name": "female", 
        "path": "assets/female.png", 
        "dead": "assets/female_dead.png",
        "eat": "assets/female_hungry.png",
        "mate": "assets/female_love.png",
        "work": "assets/female_broke.png",
        "rest": "assets/female_rest.png"
        },
    EntityType.WORK: {"name": "work", "path": "assets/work.png"},
    EntityType.FOOD: {"name": "food", "path": "assets/food.png"}
}

additional_assets = {
    EntityType.PERSON_MALE: {"name": "heart", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.PERSON_FEMALE: {"name": "heart", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.WORK: {"name": "working", "path": "assets/working_{}.png", "count": 3},
}


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class ActionType(Enum):
    EAT = "eat"
    WORK = "work"
    REST = "rest"
    MATE = "mate"
    SEARCH = "search"

class ResourceType(Enum):
    FOOD = "food"
    MONEY = "money"
    ENERGY = "energy"
