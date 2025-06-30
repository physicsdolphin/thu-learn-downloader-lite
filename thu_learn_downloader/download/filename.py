import re
from pathlib import Path

from thu_learn_downloader.client.course import Course
from thu_learn_downloader.client.document import Document, DocumentClass
from thu_learn_downloader.client.homework import Attachment, Homework
from thu_learn_downloader.client.semester import Semester


def document(
    prefix: Path,
    semester: Semester,
    course: Course,
    document_class: DocumentClass,
    document: Document,
    index: int,
) -> Path:

    def sanitize(name: str) -> str:
        # Replace invalid Windows characters with underscores
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.strip())
        return name.rstrip(' .')

    filename: Path = (
        prefix
        / sanitize(semester.id)
        / sanitize(course.name)
        / "docs"
        / sanitize(document_class.title)
        / sanitize(f"{index:02d}-{document.title}")
    )
    if document.file_type:
        filename = filename.with_suffix("." + document.file_type)
    return filename


def homework(
    prefix: Path, semester: Semester, course: Course, homework: Homework
) -> Path:

    def sanitize(name: str) -> str:
        # Replace invalid Windows characters with underscores
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.strip())
        return name.rstrip(' .')

    return (
            prefix
            / sanitize(semester.id)
            / sanitize(course.name)
            / "work"
            / sanitize(f"{homework.number:02d}-{homework.title}")
            / "README.md"
    )

def attachment(
    prefix: Path,
    semester: Semester,
    course: Course,
    homework: Homework,
    attachment: Attachment,
) -> Path:

    def sanitize(name: str) -> str:
        # Replace invalid Windows characters with underscores
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.strip())
        return name.rstrip(' .')

    filename: Path = Path(sanitize(attachment.name))
    filename = filename.with_stem(
        f"{homework.number:02d}-{homework.title}-{attachment.type_}".replace(
            "/", "-slash-"
        )
    )
    return (
        prefix
        / sanitize(semester.id)
        / sanitize(course.name)
        / "work"
        / sanitize(f"{homework.number:02d}-{homework.title}")
        / filename
    )
