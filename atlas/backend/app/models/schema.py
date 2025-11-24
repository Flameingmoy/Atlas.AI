from typing import Optional, Any, Dict
from sqlmodel import SQLModel, Field, Column
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
import uuid

class POI(SQLModel, table=True):
    __tablename__ = "pois"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    category: str
    subcategory: Optional[str] = None
    # SRID 4326 = WGS 84 (Lat/Lon)
    location: Any = Field(sa_column=Column(Geometry("POINT", srid=4326))) 
    metadata_json: Dict = Field(default={}, sa_column=Column(JSONB))

class Demographic(SQLModel, table=True):
    __tablename__ = "demographics"
    
    # H3 Index (Resolution 9) as the primary key
    h3_index: str = Field(primary_key=True)
    
    population_density: float
    median_income: int
    traffic_score: float
    
    # Optional: Store the polygon geometry for easier visualization if needed, 
    # but we can also generate it on the fly. Let's store it for convenience in this prototype.
    boundary: Any = Field(sa_column=Column(Geometry("POLYGON", srid=4326)))
