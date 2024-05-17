from enum import Enum

class ItemTypes(Enum):
    MENTAH = "mentah"
    JADI = "jadi"
    
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
    
class UnitTypes(Enum):
    KG = "kg"
    PCS = "pcs"
    METER = "meter"
    
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
    
class TypeTypes(Enum):
    PURCHASE = "purchase"
    SALES = "sales"
        
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]