import os
import importlib
import json

from typing import Optional, Iterable, List, Tuple
from datetime import datetime
from sqlalchemy import (
    insert,
    update,
    select,
    Text,
    DateTime,
    Table,
    Column,
    String,
    Integer,
    Boolean,
    MetaData,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from alembic.config import Config
from alembic import command
from docassemble.base.util import DARedis, log
from docassemble.base.sql import alchemy_url, connect_args

__all__ = [
    "save_feedback_info",
    "set_feedback_github_url",
    "redis_panel_emails_key",
    "add_panel_participant",
    "potential_panelists",
    "mark_archived",
    "get_all_feedback_info",
    "save_good_or_bad",
    "get_good_or_bad",
]

redis_panel_emails_key = "docassemble-GithubFeedbackForm:panel_emails"

############################################
## Panel particitpants are managed through a Redis ZSet (a sorted/scored set).
## The score is the timestamp of when they responded, so we can fetch newer
## respondents (more likely to accept a follow up interview).
## https://redis.io/docs/manual/data-types/#sorted-sets


def add_panel_participant(email: str):
    """Adds this email to a list of potential participants for a qualitative research panel.
    Adds the email and when they responded, as we shouldn't link their feedback to their identity at all.
    """
    red = DARedis()
    red.zadd(redis_panel_emails_key, {email: datetime.now().timestamp()})


def potential_panelists() -> Iterable[Tuple[str, datetime]]:
    red = DARedis()
    return [
        (item, datetime.fromtimestamp(score))
        for item, score in red.zrange(redis_panel_emails_key, 0, -1, withscores=True)
    ]


###################################
## Using SQLAlchemy to save / retrieve session information that is linked
## to specific feedback issues, or just to store private feedback


def upgrade_db(url, py_file, engine, version_table, conn_args):
    """A stripped down version of `docassemble.base.sql:upgrade_db`,
    that does not `stamp` ever; it always tries to upgrade from scratch.

    Assumes that the upgrade functions in alembic have checks for existing
    columns and tables.
    """
    packagedir = os.path.dirname(os.path.abspath(py_file))
    alembic_path = os.path.join(packagedir, "alembic")
    if not os.path.isdir(alembic_path):
        return
    ini_file = os.path.join(packagedir, "alembic.ini")
    if not os.path.isfile(ini_file):
        log(f"alembic.ini file not found at {ini_file}")
        return
    versions_path = os.path.join(alembic_path, "versions")
    if not os.path.isdir(versions_path):
        os.makedirs(versions_path, exist_ok=True)
    alembic_cfg = Config(ini_file)
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    alembic_cfg.set_main_option("connect_args", json.dumps(conn_args))
    alembic_cfg.set_main_option("script_location", alembic_path)
    command.upgrade(alembic_cfg, "head")


Base = declarative_base()
metadata_obj = Base.metadata

## This table functions as both storage for bug report-session links,
## and for more general on-server feedback, prompted for at the end of interviews
feedback_session_table = Table(
    "feedback_session",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("interview", String),
    Column("session_id", String),
    Column("body", Text),
    Column("html_url", String),
    Column("archived", Boolean),
    Column("datetime", DateTime),
)

good_or_bad_table = Table(
    "good_or_bad",
    metadata_obj,
    Column("reaction", Integer),
    Column("interview", String),
    Column("version", String),
    Column("datetime", DateTime),
)


db_url = alchemy_url("db")
conn_args = connect_args("db")
engine = create_engine(db_url, connect_args=conn_args)

metadata_obj.create_all(engine)
metadata_obj.bind = engine

upgrade_db(
    db_url,
    __file__,
    engine,
    version_table="al_feedback_on_server_version",
    conn_args=conn_args,
)


def save_feedback_info(
    interview: str, *, session_id: Optional[str] = None, template=None, body=None
) -> Optional[str]:
    """Saves feedback along with optional session information in a SQL DB"""
    if template:
        body = template.content

    if interview and (session_id or body):
        stmt = insert(feedback_session_table).values(
            interview=interview,
            session_id=session_id,
            body=body,
            datetime=datetime.now(),
            archived=False,
        )
        with engine.begin() as conn:
            result = conn.execute(stmt)
            id_for_feedback = result.inserted_primary_key[0]

        return id_for_feedback
    else:  # can happen if the forwarding interview didn't pass session info
        log(
            f"feedback_on_server: Unable to save this feedback in DB: interview: {interview}, session_id: {session_id}, body: {body}"
        )
        return None


def set_feedback_github_url(id_for_feedback: str, github_url: str) -> bool:
    """Returns true if save was successful"""
    stmt = (
        update(feedback_session_table)
        .where(feedback_session_table.c.id == id_for_feedback)
        .values(html_url=github_url)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
    if result.rowcount == 0:
        log(f"Cannot find {id_for_feedback} in DB")
        return False
    return True


def mark_archived(id_for_feedback: str) -> bool:
    stmt = (
        update(feedback_session_table)
        .where(feedback_session_table.c.id == id_for_feedback)
        .values(archived=True)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
    if result.rowcount == 0:
        log(f"Cannot find {id_for_feedback} in DB")
        return False
    return True


def get_all_feedback_info(interview=None, include_archived=False) -> Iterable:
    stmt = select(feedback_session_table)
    if interview:
        stmt = stmt.where(feedback_session_table.c.interview == interview)
    if not include_archived:
        stmt = stmt.where(feedback_session_table.c.archived == False)
    with engine.begin() as conn:
        results = conn.execute(stmt)
        # Turn into literal dict because DA is too eager to save / load SQLAlchemy objects into the interview SQL
        return {str(row["id"]): dict(row) for row in results.mappings()}


def save_good_or_bad(
    reaction: int,
    *,
    user_info_object=None,
    interview: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
    """Saves a user's reaction to an interview, in the form of an int (0 being
    neutral, positive numbers being good, and negative numbers being bad)"""
    _package_version = None
    _interview = None
    if user_info_object:
        _interview = user_info_object.filename
        try:
            _package_version = str(
                importlib.import_module(user_info_object.package).__version__
            )
        except:
            _package_version = "playground"

    if interview:
        _interview = interview
    if version:
        _package_version = version

    stmt = insert(good_or_bad_table).values(
        reaction=reaction,
        interview=_interview,
        version=_package_version,
        datetime=datetime.now(),
    )
    with engine.begin() as conn:
        conn.execute(stmt)


def get_good_or_bad(interview: Optional[str] = None) -> List:
    """Retrieves user's aggregate reactions to an interview (how many reactions
    and the average score of them), grouped by interview and package version"""
    stmt = select(
        good_or_bad_table.c.interview,
        good_or_bad_table.c.version,
        func.count().label("count"),
        func.avg(good_or_bad_table.c.reaction).label("average"),
    )
    if interview:
        stmt = stmt.where(good_or_bad_table.c.interview == interview)
    stmt = stmt.group_by(good_or_bad_table.c.interview, good_or_bad_table.c.version)
    with engine.begin() as conn:
        results = conn.execute(stmt)
        return [dict(row) for row in results.mappings()]
