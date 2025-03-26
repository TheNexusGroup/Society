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
    EntityType.PERSON_MALE: "assets/male.png",
    EntityType.PERSON_FEMALE: "assets/female.png",
    EntityType.WORK: "assets/work.png",
    EntityType.FOOD: "assets/food.png"
}

additional_assets = {
    EntityType.PERSON_MALE: {"name": "heart", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.PERSON_FEMALE: {"name": "heart", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.WORK: {"name": "working", "path": "assets/working_{}.png", "count": 3},
}