from enum import Enum


class Role(str, Enum):
    LEAD = "lead"
    EMPLOYEE = "employee"
    INTERN = "intern"
    SUPERUSER = "superuser"

    @classmethod
    def from_str(cls, value: str):
        value = value.strip().lower()

        for role in cls:
            if role.value == value:
                return role

        return None