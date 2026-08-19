# backend/scripts/seed_demo_data.py

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow 'python scripts/seed_demo_data.py' as well as '-m scripts.seed_demo_data'.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Application,
    Candidate,
    Job,
    JobRequirement,
    JobStatus,
    Organization,
    Resume,
    ResumeFileType,
    ResumeStatus,
    User,
    UserRole,
)

logger = logging.getLogger(__name__)

DEMO_PASSWORD = "demo-workspace-2026!"  # noqa: S105 - synthetic demo credential

ORGANIZATION_NAME = "Northwind Talent"
ORGANIZATION_SLUG = "northwind-talent"
RECRUITER_EMAIL = "recruiter@northwind.example"

JOB_TITLE = "Senior Backend Engineer"
JOB_DESCRIPTION = """Northwind Talent is hiring a senior backend engineer to
design and operate high-throughput Python services.

You will work day to day with FastAPI, PostgreSQL and Redis, own containerised
deployments on top of Docker, and help shape our event-driven architecture.

Requirements:
- 5+ years building production backend services
- Strong Python and FastAPI experience
- Deep PostgreSQL knowledge, including query tuning
- Comfortable owning services in production
"""

REQUIRED_SKILLS = ["Python", "FastAPI", "PostgreSQL"]
PREFERRED_SKILLS = ["Redis", "Docker", "Kubernetes"]
MIN_EXPERIENCE_YEARS = 5

# (name, email, resume_text). Deliberately spans the score range so the
# dashboard shows a distribution rather than a single cluster.
DEMO_CANDIDATES: list[tuple[str, str, str]] = [
    (
        "Priya Raghavan",
        "priya.raghavan@example.com",
        """Priya Raghavan
priya.raghavan@example.com | +91 98765 43210
github.com/priya-raghavan/redis-cache-layer

Professional Summary
Backend engineer with 7 years of professional experience building
high-throughput Python services.

Skills
Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes

Experience
Senior Backend Engineer, Acme Logistics
Designed event-driven services sustaining 40,000 requests per second.
Cut p99 latency from 850ms to 120ms with a Redis cache layer.

Projects
Multi-tenant API caching layer

Education
B.Tech, Computer Science
""",
    ),
    (
        "Daniel Okafor",
        "daniel.okafor@example.com",
        """Daniel Okafor
daniel.okafor@example.com
daniel.okafor@example.com

Professional Summary
Backend developer with 4 years of professional experience.

Skills
Python, Django, PostgreSQL, Docker

Experience
Backend Developer, Example Retail
Built internal reporting services and REST APIs.

Education
BSc, Software Engineering
""",
    ),
    (
        "Mei Lin Chen",
        "meilin.chen@example.com",
        """Mei Lin Chen
meilin.chen@example.com

Professional Summary
Full-Stack engineer with 6 years of professional experience.

Skills
JavaScript, TypeScript, React, Node.js, PostgreSQL

Experience
Full-Stack Engineer, Example Media
Owned the customer-facing web application end to end.

Projects
Realtime dashboard with websocket streaming

Education
BEng, Information Systems
""",
    ),
    (
        "Tomas Novak",
        "tomas.novak@example.com",
        """Tomas Novak
tomas.novak@example.com

Professional Summary
Graphic designer moving into product design.

Skills
Figma, Adobe Illustrator, Photoshop, typography

Experience
Designer, Example Studio

Education
BA, Visual Communication
""",
    ),
]


def _get_or_create_organization(db: Session) -> Organization:
    existing = db.scalar(
        select(Organization).where(Organization.slug == ORGANIZATION_SLUG)
    )
    if existing is not None:
        logger.info("Organization already present; reusing it")
        return existing

    organization = Organization(name=ORGANIZATION_NAME, slug=ORGANIZATION_SLUG)
    db.add(organization)
    db.flush()
    return organization


def _get_or_create_recruiter(db: Session, organization: Organization) -> User:
    existing = db.scalar(select(User).where(User.email == RECRUITER_EMAIL))
    if existing is not None:
        return existing

    user = User(
        email=RECRUITER_EMAIL,
        full_name="Demo Recruiter",
        password_hash=hash_password(DEMO_PASSWORD),
        organization_id=organization.id,
        role=UserRole.ORGANIZATION_ADMIN,
    )
    db.add(user)
    db.flush()
    return user


def _get_or_create_job(
    db: Session, organization: Organization, creator: User
) -> Job:
    existing = db.scalar(
        select(Job).where(
            Job.organization_id == organization.id, Job.title == JOB_TITLE
        )
    )
    if existing is not None:
        return existing

    job = Job(
        organization_id=organization.id,
        created_by=creator.id,
        title=JOB_TITLE,
        description=JOB_DESCRIPTION,
        location="Bengaluru (Hybrid)",
        employment_type="FULL_TIME",
        status=JobStatus.PUBLISHED,
        is_public=True,
        min_experience_years=MIN_EXPERIENCE_YEARS,
    )
    db.add(job)
    db.flush()

    for skill in REQUIRED_SKILLS:
        db.add(JobRequirement(job_id=job.id, skill=skill, is_required=True))
    for skill in PREFERRED_SKILLS:
        db.add(JobRequirement(job_id=job.id, skill=skill, is_required=False))
    db.flush()
    return job


def _seed_applications(
    db: Session, organization: Organization, job: Job
) -> list[Application]:
    applications: list[Application] = []

    for index, (name, email, resume_text) in enumerate(DEMO_CANDIDATES):
        candidate = db.scalar(
            select(Candidate).where(
                Candidate.organization_id == organization.id,
                Candidate.email == email,
            )
        )
        if candidate is None:
            candidate = Candidate(
                organization_id=organization.id,
                full_name=name,
                email=email,
            )
            db.add(candidate)
            db.flush()

        existing_application = db.scalar(
            select(Application).where(
                Application.job_id == job.id,
                Application.candidate_id == candidate.id,
            )
        )
        if existing_application is not None:
            applications.append(existing_application)
            continue

        resume = Resume(
            organization_id=organization.id,
            candidate_id=candidate.id,
            original_filename=f"{name.lower().replace(' ', '_')}.pdf",
            stored_filename=f"demo_resume_seed_{index}.pdf",
            file_type=ResumeFileType.PDF,
            mime_type="application/pdf",
            file_size_bytes=len(resume_text.encode("utf-8")),
            # Synthetic digest: no real file is written by the seeder.
            sha256="0" * 64,
            status=ResumeStatus.PARSED,
            extracted_text=resume_text,
        )
        db.add(resume)
        db.flush()

        application = Application(
            organization_id=organization.id,
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id,
        )
        db.add(application)
        db.flush()
        applications.append(application)

    return applications


def seed(*, run_screening: bool = True) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with SessionLocal() as db:
        organization = _get_or_create_organization(db)
        recruiter = _get_or_create_recruiter(db, organization)
        job = _get_or_create_job(db, organization, recruiter)
        applications = _seed_applications(db, organization, job)
        db.commit()

        print(f"Organization : {organization.name} ({organization.slug})")
        print(f"Recruiter    : {recruiter.email} / {DEMO_PASSWORD}")
        print(f"Job          : {job.title}")
        print(f"Applications : {len(applications)}")

        if not run_screening:
            print("\nRun with --screen to score these applications now.")
            return

        # Imported here so the seeder works even when the pipeline's optional
        # AI dependencies are absent.
        from app.services.screening_service import screen_application

        print("\nScreening:")
        for application in applications:
            result = screen_application(
                db,
                application_id=application.id,
                organization_id=organization.id,
                actor_user_id=recruiter.id,
            )
            flagged = " [FAIRNESS REVIEW]" if result.bias_review_required else ""
            print(
                f"  {result.overall_score:>5.1f} ({result.recommendation:<13}"
                f" provider={result.provider:<8}"
                f" semantic={result.semantic_backend}{flagged})"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--screen",
        action="store_true",
        help="Run the screening pipeline over the seeded applications",
    )
    args = parser.parse_args()

    try:
        seed(run_screening=args.screen)
    except Exception:
        logger.exception("Seeding failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())