from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, require_roles, get_current_user_optional

router = APIRouter()


def _authorize_meeting_access(
    db: Session,
    meeting: models.TutorMeeting,
    current_user: models.User,
) -> bool:
    """Return True if the user can view/modify this meeting."""
    if current_user.role in (models.Role.ADMIN, models.Role.TEACHER):
        return True
    # student_id is a FK to the students table, not users table.
    # Check ownership via Student.owner_user_id.
    student = crud.get_student(db, meeting.student_id)
    if student and student.owner_user_id == current_user.id:
        return True
    if meeting.tutor_id == current_user.id:
        return True
    return False


def _student_belongs_to_user(db: Session, student_id: str, user_id: str) -> bool:
    student = crud.get_student(db, student_id)
    if not student:
        return False
    return student.owner_user_id == user_id


@router.post("/meetings", response_model=schemas.TutorMeetingResponse, status_code=201)
def create_meeting(
    *,
    db: Session = Depends(get_db),
    meeting_in: schemas.TutorMeetingCreate,
    current_user: models.User = Depends(get_current_user),
) -> models.TutorMeeting:
    # Students may only create meetings for students they own
    if current_user.role == models.Role.STUDENT:
        if not _student_belongs_to_user(db, meeting_in.student_id, current_user.id):
            raise HTTPException(status_code=403, detail="Can only request meetings for your own student profile")
    return crud.create_tutor_meeting(db, meeting_in)


@router.get("/meetings", response_model=list[schemas.TutorMeetingResponse])
def read_meetings(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    student_id: str | None = None,
    course_id: str | None = None,
    current_user: models.User = Depends(get_current_user),
) -> list[models.TutorMeeting]:
    # Admins/teachers can filter broadly
    if current_user.role in (models.Role.ADMIN, models.Role.TEACHER):
        if student_id:
            return crud.get_tutor_meetings_by_student(db, student_id)
        if course_id:
            return crud.get_tutor_meetings_by_course(db, course_id)
        return crud.get_all_tutor_meetings(db, skip=skip, limit=limit)

    # Students: show meetings for any student profile they own.
    # First get all student IDs owned by this user, then filter meetings.
    owned_students = (
        db.query(models.Student)
        .filter(models.Student.owner_user_id == current_user.id)
        .all()
    )
    student_ids = [s.id for s in owned_students]
    if not student_ids:
        return []
    query = db.query(models.TutorMeeting).filter(models.TutorMeeting.student_id.in_(student_ids))
    if course_id:
        query = query.filter(models.TutorMeeting.course_id == course_id)
    return query.order_by(models.TutorMeeting.created_at.desc()).all()


@router.get("/meetings/{meeting_id}", response_model=schemas.TutorMeetingResponse)
def read_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.TutorMeeting:
    meeting = crud.get_tutor_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not _authorize_meeting_access(db, meeting, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view this meeting")
    return meeting


@router.put("/meetings/{meeting_id}", response_model=schemas.TutorMeetingResponse)
def update_meeting(
    meeting_id: str,
    meeting_in: schemas.TutorMeetingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.TutorMeeting:
    meeting = crud.get_tutor_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Students can only update their own meetings, and only limited fields (notes, cancel)
    if current_user.role == models.Role.STUDENT:
        if not _authorize_meeting_access(db, meeting, current_user):
            raise HTTPException(status_code=403, detail="Not authorized")
        # Students cannot assign tutors or change status to scheduled
        if meeting_in.tutor_id is not None or meeting_in.meeting_url is not None:
            raise HTTPException(status_code=403, detail="Cannot assign tutor or meeting URL")

    # Tutors/teachers can update any meeting (assign themselves, schedule, etc.)
    updated = crud.update_tutor_meeting(db, meeting_id, meeting_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return updated


@router.delete("/meetings/{meeting_id}", status_code=204)
def delete_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> None:
    meeting = crud.get_tutor_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not _authorize_meeting_access(db, meeting, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this meeting")
    deleted = crud.delete_tutor_meeting(db, meeting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
