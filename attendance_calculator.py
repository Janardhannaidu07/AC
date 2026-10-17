from dataclasses import dataclass
from enum import Enum
from typing import List


class SessionType(Enum):
    LECTURE = 1
    LAB = 2

    @property
    def weight(self) -> int:
        return self.value


class AttendanceStatus(Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


@dataclass
class Subject:
    id: str
    name: str = ""
    target_percentage: float = 75.0


@dataclass
class AttendanceRecord:
    subject_id: str
    session_type: SessionType
    status: AttendanceStatus


@dataclass
class SubjectSummary:
    subject: Subject
    held_units: int
    attended_units: int
    percentage: float
    can_skip_next: bool
    safe_skips_remaining: int
    classes_needed_to_recover: int


class AttendanceCalculator:
    @staticmethod
    def calculate_percentage(attended_units: int, held_units: int) -> float:
        if held_units == 0:
            return 100.0
        return (attended_units / held_units) * 100.0

    @staticmethod
    def calculate_safe_skips(attended_units: int, held_units: int, target_percentage: float) -> int:
        if held_units == 0:
            return 0
        skips = 0
        while AttendanceCalculator.calculate_percentage(attended_units, held_units + skips + 1) >= target_percentage:
            skips += 1
        return skips

    @staticmethod
    def calculate_recovery_classes(attended_units: int, held_units: int, target_percentage: float) -> int:
        if AttendanceCalculator.calculate_percentage(attended_units, held_units) >= target_percentage:
            return 0
        needed = 0
        while AttendanceCalculator.calculate_percentage(attended_units + needed + 1, held_units + needed + 1) < target_percentage:
            needed += 1
        return needed + 1

    @staticmethod
    def build_summary(subject: Subject, records: List[AttendanceRecord]) -> SubjectSummary:
        subject_records = [r for r in records if r.subject_id == subject.id]
        held_units = sum(r.session_type.weight for r in subject_records)
        attended_units = sum(
            r.session_type.weight for r in subject_records if r.status == AttendanceStatus.PRESENT
        )
        percentage = AttendanceCalculator.calculate_percentage(attended_units, held_units)
        safe_skips_remaining = AttendanceCalculator.calculate_safe_skips(
            attended_units, held_units, subject.target_percentage
        )
        classes_needed_to_recover = AttendanceCalculator.calculate_recovery_classes(
            attended_units, held_units, subject.target_percentage
        )
        return SubjectSummary(
            subject=subject,
            held_units=held_units,
            attended_units=attended_units,
            percentage=percentage,
            can_skip_next=safe_skips_remaining > 0,
            safe_skips_remaining=safe_skips_remaining,
            classes_needed_to_recover=classes_needed_to_recover,
        )


# --- quick sanity check against the same boundary cases used earlier ---
if __name__ == "__main__":
    def check(label, cond):
        print(("PASS" if cond else "FAIL"), "-", label)

    ac = AttendanceCalculator
    check("exactly 75% -> 0 safe skips", ac.calculate_safe_skips(30, 40, 75.0) == 0)
    check("87.5% -> 6 safe skips", ac.calculate_safe_skips(35, 40, 75.0) == 6)
    check("50% -> 40 units to recover", ac.calculate_recovery_classes(20, 40, 75.0) == 40)

    subj = Subject(id="s1", name="DS", target_percentage=75.0)
    records = [
        AttendanceRecord("s1", SessionType.LAB, AttendanceStatus.PRESENT),
        AttendanceRecord("s1", SessionType.LECTURE, AttendanceStatus.ABSENT),
    ]
    summary = ac.build_summary(subj, records)
    check("lab counts as 2 held units", summary.held_units == 3)
    check("lab attended -> 2 attended units", summary.attended_units == 2)
    check("percentage ~ 66.67", abs(summary.percentage - 66.67) < 0.01)
