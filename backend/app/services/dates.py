import calendar
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import settings


def get_app_timezone() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def get_local_now() -> datetime:
    return datetime.now(get_app_timezone())


def resolve_due_day(year: int, month: int, due_day: int) -> int:
    last_day = calendar.monthrange(year, month)[1]
    return min(max(due_day, 1), last_day)


def due_date_for_month(year: int, month: int, due_day: int) -> date:
    return date(year, month, resolve_due_day(year, month, due_day))


def next_due_date(from_date: date, due_day: int) -> date:
    current_month_due = due_date_for_month(from_date.year, from_date.month, due_day)
    if current_month_due >= from_date:
        return current_month_due

    if from_date.month == 12:
        return due_date_for_month(from_date.year + 1, 1, due_day)
    return due_date_for_month(from_date.year, from_date.month + 1, due_day)


def due_datetime_for_reference(reference_dt: datetime, due_day: int) -> datetime:
    local_reference = reference_dt.astimezone(get_app_timezone())
    due_date = next_due_date(local_reference.date(), due_day)
    return datetime.combine(due_date, time(23, 59, 59), tzinfo=get_app_timezone())
