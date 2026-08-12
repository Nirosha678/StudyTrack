
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentBase(BaseModel):
    name: str
    email: str
    age: int = Field(gt=0, description="Age must be a positive number")

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value: str) -> str:
       
        if "@" not in value:
            raise ValueError("email must contain an '@' character")
        return value


class StudentCreate(StudentBase):
    
    pass


class StudentUpdate(BaseModel):
    
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and "@" not in value:
            raise ValueError("email must contain an '@' character")
        return value


class CourseBase(BaseModel):
    course_name: str
    credits: int = Field(ge=1, le=6, description="Credits must be between 1 and 6")
    student_id: int


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
 
    course_name: Optional[str] = None
    credits: Optional[int] = Field(default=None, ge=1, le=6)
    student_id: Optional[int] = None


class CourseResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class StudentResponse(StudentBase):
    id: int
    courses: list[CourseResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
