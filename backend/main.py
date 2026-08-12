from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import crud
import algorithms
import ai_service

from database import Base, SessionLocal, engine, get_db
from seed_data import seed_if_empty
import schemas


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="StudyTrack API",
    description="Student and Course Management API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP - SEED DATABASE
# ============================================================

@app.on_event("startup")
def on_startup():
    db = SessionLocal()

    try:
        seed_if_empty(db)
    finally:
        db.close()


# ============================================================
# STUDENT ROUTES
# ============================================================

@app.post(
    "/students/",
    response_model=schemas.StudentResponse,
    status_code=201
)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db)
):
    existing = crud.get_student_by_email(
        db,
        student.email
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A student with this email already exists"
        )

    return crud.create_student(db, student)


@app.get(
    "/students/",
    response_model=List[schemas.StudentResponse]
)
def list_students(
    min_age: Optional[int] = Query(
        default=None,
        gt=0
    ),
    db: Session = Depends(get_db)
):
    return crud.get_students(
        db,
        min_age=min_age
    )


# ============================================================
# INSERTION SORT
# ============================================================

@app.get("/students/sorted")
def sorted_students(
    by: str = Query(default="age"),
    db: Session = Depends(get_db)
):
    if by not in ("age", "name"):
        raise HTTPException(
            status_code=400,
            detail="`by` must be 'age' or 'name'"
        )

    students = crud.get_students(db)

    student_list = []

    for student in students:
        student_list.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "age": student.age
        })

    algorithms.insertion_sort_by_field(
        student_list,
        by
    )

    return student_list


# ============================================================
# BINARY SEARCH
# ============================================================

@app.get("/students/search")
def search_student_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    students = crud.get_students(db)

    student_list = []

    for student in students:
        student_list.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "age": student.age
        })

    # Assignment requirement:
    # Use Python's built-in sorted() before binary search.
    name_sorted = sorted(
        student_list,
        key=lambda student: student["name"]
    )

    result = algorithms.binary_search_by_name(
        name_sorted,
        name
    )

    if result == -1:
        raise HTTPException(
            status_code=404,
            detail=f"No student named '{name}' found"
        )

    return result


# ============================================================
# ROSTER REPORT
# ============================================================

@app.get("/students/report")
def students_report(
    min_age: int = Query(default=21),
    db: Session = Depends(get_db)
):
    students = crud.get_students(db)

    student_list = []

    for student in students:
        student_list.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "age": student.age
        })

    report = algorithms.format_roster_report(
        student_list
    )

    count = algorithms.count_students_meeting_min_age(
        student_list,
        min_age
    )

    return {
        "report": report,
        "count_meeting_min_age": count
    }


# ============================================================
# GET ONE STUDENT
# ============================================================

@app.get(
    "/students/{student_id}",
    response_model=schemas.StudentResponse
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = crud.get_student(
        db,
        student_id
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


# ============================================================
# UPDATE STUDENT
# ============================================================

@app.patch(
    "/students/{student_id}",
    response_model=schemas.StudentResponse
)
def update_student(
    student_id: int,
    updates: schemas.StudentUpdate,
    db: Session = Depends(get_db)
):
    # Check whether the new email already belongs
    # to another student.
    if updates.email is not None:
        existing = crud.get_student_by_email(
            db,
            updates.email
        )

        if (
            existing is not None
            and existing.id != student_id
        ):
            raise HTTPException(
                status_code=409,
                detail="A student with this email already exists"
            )

    student = crud.update_student(
        db,
        student_id,
        updates
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


# ============================================================
# DELETE STUDENT
# ============================================================

@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = crud.delete_student(
        db,
        student_id
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "detail": "Student deleted",
        "id": student_id
    }


# ============================================================
# STUDENT COURSE COUNT
# ============================================================

@app.get("/students/{student_id}/course-count")
def student_course_count(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = crud.get_student(
        db,
        student_id
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    count = crud.get_student_course_count(
        db,
        student_id
    )

    return {
        "student_id": student_id,
        "course_count": count
    }


# ============================================================
# COURSE ROUTES
# ============================================================

@app.post(
    "/courses/",
    response_model=schemas.CourseResponse,
    status_code=201
)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db)
):
    student = crud.get_student(
        db,
        course.student_id
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="student_id does not exist"
        )

    return crud.create_course(
        db,
        course
    )


@app.get(
    "/courses/",
    response_model=List[schemas.CourseResponse]
)
def list_courses(
    db: Session = Depends(get_db)
):
    return crud.get_courses(db)


@app.get(
    "/courses/{course_id}",
    response_model=schemas.CourseResponse
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = crud.get_course(
        db,
        course_id
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return course


@app.patch(
    "/courses/{course_id}",
    response_model=schemas.CourseResponse
)
def update_course(
    course_id: int,
    updates: schemas.CourseUpdate,
    db: Session = Depends(get_db)
):
    # If student_id is being changed,
    # make sure the new student exists.
    if updates.student_id is not None:
        student = crud.get_student(
            db,
            updates.student_id
        )

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

    course = crud.update_course(
        db,
        course_id,
        updates
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return course


@app.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = crud.delete_course(
        db,
        course_id
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return {
        "detail": "Course deleted",
        "id": course_id
    }


# ============================================================
# AI ASSISTANT - SUMMARIZE
# ============================================================

@app.post("/assistant/summarize")
def assistant_summarize(payload: dict):
    text = payload.get("text", "")

    return ai_service.summarize_notes(text)


# ============================================================
# AI ASSISTANT - SEARCH NOTES
# ============================================================

@app.get("/assistant/search")
def assistant_search(
    query: str = ""
):
    return {
        "results": ai_service.search_notes(query)
    }


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="../frontend",
        html=True
    ),
    name="static"
)