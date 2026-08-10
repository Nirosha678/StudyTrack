
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


def get_students(db: Session, min_age: Optional[int] = None):
    query = db.query(models.Student)
    if min_age is not None:
        query = query.filter(models.Student.age >= min_age)
    return query.all()


def get_student(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_student_by_email(db: Session, email: str):
    return db.query(models.Student).filter(models.Student.email == email).first()


def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(
        name=student.name, email=student.email, age=student.age
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(db: Session, student_id: int, updates: schemas.StudentUpdate):
    db_student = get_student(db, student_id)
    if db_student is None:
        return None
  
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_student, field, value)
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: int):
    db_student = get_student(db, student_id)
    if db_student is None:
        return None
    db.delete(db_student)
    db.commit()
    return db_student


def get_student_course_count(db: Session, student_id: int) -> int:
   
    return (
        db.query(func.count(models.Course.id))
        .filter(models.Course.student_id == student_id)
        .scalar()
    )


def get_courses(db: Session):
    return db.query(models.Course).all()


def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def create_course(db: Session, course: schemas.CourseCreate) -> models.Course:
    db_course = models.Course(
        course_name=course.course_name,
        credits=course.credits,
        student_id=course.student_id,
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course_id: int, updates: schemas.CourseUpdate):
    db_course = get_course(db, course_id)
    if db_course is None:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_course, field, value)
    db.commit()
    db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: int):
    db_course = get_course(db, course_id)

    if db_course is None:
        return None

    db.delete(db_course)
    db.commit()
    return db_course
