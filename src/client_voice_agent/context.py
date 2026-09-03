"""Synthetic data and approved help content for the reference demo."""

from calendar import day_name, month_name
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DemoRecord:
    """A fictional organization and one prepared document request."""

    organization_name: str
    contact_name: str
    required_document: str
    upload_deadline: date
    upload_path: tuple[str, ...]

    @property
    def spoken_deadline(self) -> str:
        """Return the deadline in an unambiguous spoken form."""
        value = self.upload_deadline
        return (
            f"{day_name[value.weekday()]}, {month_name[value.month]} "
            f"{value.day}, {value.year}"
        )

    @property
    def spoken_upload_path(self) -> str:
        """Return the fictional navigation path in spoken form."""
        return ", then ".join(self.upload_path)


DEMO_RECORD = DemoRecord(
    organization_name="Juniper Works, LLC",
    contact_name="Sam Rivera",
    required_document="current certificate of insurance",
    upload_deadline=date(2026, 9, 18),
    upload_path=("Demo Portal", "Open Requests", "Upload Document"),
)

UPLOAD_HELP = (
    "Accepted demo file types are PDF, PNG, and JPG. The demo file-size limit is "
    "10 MB. If a file is larger, ask the caller to use a smaller export."
)

SUPPORT_EMAIL = "support@example.com"


def render_demo_record(record: DemoRecord = DEMO_RECORD) -> str:
    """Render the fixed record for the assistant instructions."""
    return (
        f"Organization: {record.organization_name}\n"
        f"Contact: {record.contact_name}\n"
        f"Required document: {record.required_document}\n"
        f"Upload deadline: {record.spoken_deadline}\n"
        f"Fictional upload path: {record.spoken_upload_path}"
    )
