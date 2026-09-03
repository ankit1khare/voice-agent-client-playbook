"""Synthetic business record and approved help content for the Rho demo."""

from calendar import day_name, month_name
from dataclasses import dataclass
from datetime import date

RHO_APPLYING_FAQ_URL = (
    "https://www.rho.co/help-center/general-rho-information/applying-to-rho-faqs"
)
RHO_HELP_CENTER_URL = "https://www.rho.co/help-center"


@dataclass(frozen=True, slots=True)
class DemoBusinessRecord:
    """A fictional business and its prepared missing-document details."""

    business_name: str
    contact_name: str
    missing_document: str
    document_month: str
    upload_deadline: date
    upload_path: tuple[str, ...]

    @property
    def spoken_deadline(self) -> str:
        """Return the deadline in unambiguous spoken form."""
        value = self.upload_deadline
        return (
            f"{day_name[value.weekday()]}, {month_name[value.month]} "
            f"{value.day}, {value.year}"
        )

    @property
    def spoken_upload_path(self) -> str:
        """Return the fictional upload path in spoken form."""
        return ", then ".join(self.upload_path)


DEMO_BUSINESS = DemoBusinessRecord(
    business_name="Northstar Labs, Inc.",
    contact_name="Maya Chen",
    missing_document="bank statement",
    document_month="August 2026",
    upload_deadline=date(2026, 9, 14),
    upload_path=("Rho Demo Portal", "Required Documents", "Upload"),
)

UPLOAD_HELP = (
    "If a file is zipped or compressed, unzip it before uploading. "
    "Use a file type supported by the upload section. The maximum file size is "
    "10 MB. If an image is larger, reduce its size. If a PDF, CSV, DOC, XLS, or "
    "XLSX file is larger, split it into smaller parts."
)

RHO_SUPPORT_PHONE_SPOKEN = "855-743-8746"
RHO_SUPPORT_EMAIL = "clientservice@rho.co"


def render_demo_record(record: DemoBusinessRecord = DEMO_BUSINESS) -> str:
    """Render the fixed record for use in the assistant instructions."""
    return (
        f"Business: {record.business_name}\n"
        f"Credit contact: {record.contact_name}\n"
        f"Missing document: {record.document_month} {record.missing_document}\n"
        f"Upload deadline: {record.spoken_deadline}\n"
        f"Fictional upload path: {record.spoken_upload_path}"
    )
