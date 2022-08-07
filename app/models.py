from pydantic import BaseModel
from pydantic.class_validators import Optional


class Photo(BaseModel):
    id: str
    description: Optional[str] = None
    image: str
