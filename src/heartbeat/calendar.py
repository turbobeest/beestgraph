"""CalDAV client for publishing beestgraph events to a Radicale calendar.

Uses the ``caldav`` library for server communication and ``icalendar`` for
building VEVENT objects.  All operations are idempotent — duplicate UIDs are
handled gracefully.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from icalendar import Calendar as iCalendar
from icalendar import Event as iEvent

from src.heartbeat.checks import CheckResult

logger = structlog.get_logger(__name__)

# iCalendar colour names (X-APPLE-CALENDAR-COLOR compatible hex).
_COLOR_OK = "#28a745"
_COLOR_WARNING = "#ffc107"
_COLOR_ERROR = "#dc3545"


class BeestgraphCalendar:
    """CalDAV client for beestgraph's calendar.

    Connects to a Radicale (or any CalDAV) server and exposes helpers for
    creating heartbeat events, pipeline events, and generic scheduled events.

    Args:
        url: Base URL of the CalDAV server.
        username: Authentication username (empty for no-auth setups).
        password: Authentication password.
        calendar_name: Display name and path slug of the calendar to use.
    """

    def __init__(
        self,
        url: str = "http://localhost:5232",
        username: str = "",
        password: str = "",
        calendar_name: str = "beestgraph",
    ) -> None:
        self._url = url.rstrip("/")
        self._username = username
        self._password = password
        self._calendar_name = calendar_name
        self._calendar: object | None = None  # caldav.Calendar once connected

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> object:
        """Return a connected ``caldav.DAVClient``.

        Returns:
            A caldav DAVClient instance.
        """
        import caldav

        kwargs: dict[str, str] = {"url": self._url}
        if self._username:
            kwargs["username"] = self._username
            kwargs["password"] = self._password  # empty string is fine for no-auth
        return caldav.DAVClient(**kwargs)

    def ensure_calendar(self) -> None:
        """Create the beestgraph calendar if it does not already exist.

        Looks for a calendar whose display name matches ``calendar_name``.
        If none is found, creates one via MKCALENDAR.
        """
        import caldav

        try:
            client = self._get_client()
            principal = client.principal()
            calendars = principal.calendars()

            for cal in calendars:
                if getattr(cal, "name", "") == self._calendar_name:
                    self._calendar = cal
                    logger.info("calendar_found", name=self._calendar_name)
                    return

            # Calendar not found — create it.
            self._calendar = principal.make_calendar(name=self._calendar_name)
            logger.info("calendar_created", name=self._calendar_name)
        except caldav.error.AuthorizationError:
            logger.error("calendar_auth_failed", url=self._url)
            raise
        except Exception as exc:
            logger.error("calendar_ensure_failed", error=str(exc))
            raise

    def _get_calendar(self) -> object:
        """Return the cached calendar object, creating it if necessary.

        Returns:
            A caldav.Calendar instance.
        """
        if self._calendar is None:
            self.ensure_calendar()
        return self._calendar  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Event creation
    # ------------------------------------------------------------------

    def add_heartbeat_event(self, checks: list[CheckResult]) -> str:
        """Create a VEVENT summarising a heartbeat cycle.

        The event has a 1-minute duration, a colour reflecting the worst
        status, and a description listing every check result.

        Args:
            checks: List of completed health-check results.

        Returns:
            The UID of the created event.
        """
        ok_count = sum(1 for c in checks if c.status == "ok")
        total = len(checks)
        worst = _worst_status(checks)

        if worst == "ok":
            summary = f"Heartbeat: {ok_count}/{total} OK"
        elif worst == "warning":
            warnings = [c.name for c in checks if c.status == "warning"]
            summary = f"Heartbeat: WARNING - {', '.join(warnings)}"
        else:
            errors = [c.name for c in checks if c.status == "error"]
            summary = f"Heartbeat: ERROR - {', '.join(errors)}"

        description_lines = [f"beestgraph heartbeat — {ok_count}/{total} checks passing", ""]
        for c in checks:
            icon = {"ok": "[OK]", "warning": "[WARN]", "error": "[ERR]"}.get(c.status, "[??]")
            description_lines.append(f"{icon} {c.name}: {c.message}")

        now = datetime.now(UTC)
        uid = self._publish_event(
            summary=summary,
            description="\n".join(description_lines),
            dtstart=now,
            dtend=now + timedelta(minutes=1),
            color=_status_color(worst),
        )
        logger.info("heartbeat_event_published", uid=uid, status=worst)
        return uid

    def add_pipeline_event(
        self,
        title: str,
        description: str,
        event_type: str = "ingestion",
        duration_minutes: int = 5,
    ) -> str:
        """Create a VEVENT for a pipeline activity (e.g. document ingestion).

        Args:
            title: Short title for the event.
            description: Longer description with processing details.
            event_type: Category tag (``ingestion``, ``processing``, etc.).
            duration_minutes: Event duration in minutes.

        Returns:
            The UID of the created event.
        """
        now = datetime.now(UTC)
        summary = f"{event_type.capitalize()}: {title}"
        uid = self._publish_event(
            summary=summary,
            description=description,
            dtstart=now,
            dtend=now + timedelta(minutes=duration_minutes),
            color=_COLOR_OK,
            categories=[event_type],
        )
        logger.info("pipeline_event_published", uid=uid, event_type=event_type, title=title)
        return uid

    def add_scheduled_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        recurrence: str | None = None,
    ) -> str:
        """Create a generic scheduled event, optionally recurring.

        Args:
            title: Event summary.
            start: Event start time (timezone-aware).
            end: Event end time (timezone-aware).
            description: Optional event description.
            recurrence: Optional iCalendar RRULE string, e.g.
                ``"FREQ=DAILY;COUNT=30"``.

        Returns:
            The UID of the created event.
        """
        uid = self._publish_event(
            summary=title,
            description=description,
            dtstart=start,
            dtend=end,
            recurrence=recurrence,
        )
        logger.info("scheduled_event_published", uid=uid, title=title)
        return uid

    def get_events(self, start: datetime, end: datetime) -> list[dict[str, str]]:
        """Query events in a date range.

        Args:
            start: Range start (timezone-aware).
            end: Range end (timezone-aware).

        Returns:
            List of dicts with ``uid``, ``summary``, ``dtstart``, ``dtend``.
        """
        try:
            cal = self._get_calendar()
            results = cal.date_search(start=start, end=end)  # type: ignore[union-attr]
            events: list[dict[str, str]] = []
            for ev in results:
                vevent = ev.vobject_instance.vevent  # type: ignore[union-attr]
                events.append(
                    {
                        "uid": str(getattr(vevent, "uid", {}).value)
                        if hasattr(vevent, "uid")
                        else "",
                        "summary": str(getattr(vevent, "summary", {}).value)
                        if hasattr(vevent, "summary")
                        else "",
                        "dtstart": str(vevent.dtstart.value) if hasattr(vevent, "dtstart") else "",
                        "dtend": str(vevent.dtend.value) if hasattr(vevent, "dtend") else "",
                    }
                )
            return events
        except Exception as exc:
            logger.error("get_events_failed", error=str(exc))
            return []

    def get_upcoming(self, hours: int = 24) -> list[dict[str, str]]:
        """Get events in the next *hours* hours.

        Args:
            hours: Look-ahead window in hours.

        Returns:
            List of event dicts (same shape as ``get_events``).
        """
        now = datetime.now(UTC)
        return self.get_events(start=now, end=now + timedelta(hours=hours))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish_event(
        self,
        *,
        summary: str,
        description: str,
        dtstart: datetime,
        dtend: datetime,
        color: str = "",
        categories: list[str] | None = None,
        recurrence: str | None = None,
    ) -> str:
        """Build an iCalendar VEVENT and push it to the CalDAV server.

        Args:
            summary: Event title.
            description: Event body text.
            dtstart: Start datetime (UTC).
            dtend: End datetime (UTC).
            color: Hex colour for calendar clients that support it.
            categories: Optional list of category tags.
            recurrence: Optional RRULE string.

        Returns:
            The UID string of the event.
        """
        uid = f"beestgraph-{uuid.uuid4()}"

        vevent = iEvent()
        vevent.add("uid", uid)
        vevent.add("dtstamp", datetime.now(UTC))
        vevent.add("dtstart", dtstart)
        vevent.add("dtend", dtend)
        vevent.add("summary", summary)
        vevent.add("description", description)

        if color:
            vevent.add("x-apple-calendar-color", color)
        if categories:
            vevent.add("categories", categories)
        if recurrence:
            vevent.add("rrule", _parse_rrule(recurrence))

        ical = iCalendar()
        ical.add("prodid", "-//beestgraph//heartbeat//EN")
        ical.add("version", "2.0")
        ical.add_component(vevent)

        try:
            cal = self._get_calendar()
            cal.save_event(ical.to_ical().decode("utf-8"))  # type: ignore[union-attr]
        except Exception as exc:
            logger.error("publish_event_failed", uid=uid, error=str(exc))
            raise

        return uid


def _worst_status(checks: list[CheckResult]) -> str:
    """Return the most severe status across all checks.

    Args:
        checks: List of check results.

    Returns:
        ``"error"``, ``"warning"``, or ``"ok"``.
    """
    if any(c.status == "error" for c in checks):
        return "error"
    if any(c.status == "warning" for c in checks):
        return "warning"
    return "ok"


def _status_color(status: str) -> str:
    """Map a status string to a hex colour.

    Args:
        status: ``"ok"``, ``"warning"``, or ``"error"``.

    Returns:
        Hex colour string.
    """
    return {"ok": _COLOR_OK, "warning": _COLOR_WARNING, "error": _COLOR_ERROR}.get(
        status, _COLOR_OK
    )


def _parse_rrule(rrule_str: str) -> dict[str, str]:
    """Parse a simple RRULE string into a dict for icalendar.

    Args:
        rrule_str: e.g. ``"FREQ=DAILY;COUNT=30"``.

    Returns:
        Dict with RRULE parameters.
    """
    result: dict[str, str] = {}
    for part in rrule_str.split(";"):
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.strip()] = val.strip()
    return result
