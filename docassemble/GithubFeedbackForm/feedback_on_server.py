import importlib

from typing import Optional, Iterable, Tuple
from datetime import datetime
from sqlalchemy import insert, update, select, Text, DateTime, Table, Column,\
    String, Integer, MetaData, create_engine, func
from docassemble.base.util import DARedis, log
from docassemble.base.sql import alchemy_url

__all__ = ['save_feedback_info', 'set_feedback_github_url', 'redis_panel_emails_key', 'add_panel_participant',
    'potential_panelists', 'get_all_feedback_info']

redis_panel_emails_key = 'docassemble-GithubFeedbackForm:panel_emails'

############################################
## Panel particitpants are managed through a Redis ZSet (a sorted/scored set).
## The score is the timestamp of when they responded, so we can fetch newer
## respondents (more likely to accept a follow up interview).
## https://redis.io/docs/manual/data-types/#sorted-sets

def add_panel_participant(email:str):
    """Adds this email to a list of potential participants for a qualitative research panel.
    Adds the email and when they responded, as we shouldn't link their feedback to their identity at all.
    """
    red = DARedis()
    red.zadd(redis_panel_emails_key, {email: datetime.now().timestamp()})

def potential_panelists() -> Iterable[Tuple[str, datetime]]:
    red = DARedis()
    return [(item, datetime.fromtimestamp(score)) for item, score in red.zrange(redis_panel_emails_key, 0, -1, withscores=True)]

###################################
## Using SQLAlchemy to save / retrieve session information that is linked
## to specific feedback issues

db_url = alchemy_url('db')
engine = create_engine(db_url)

metadata_obj = MetaData()

## This table functions as both storage for bug report-session links,
## and for more general on-server feedback, prompted for at the end of interviews
feedback_session_table = Table(
  "feedback_session",
  metadata_obj,
  Column('id', Integer, primary_key=True),
  Column('interview', String),
  Column('session_id', String),
  Column('body', Text),
  Column('html_url', String)
)

metadata_obj.create_all(engine)

def save_feedback_info(interview, *, session_id=None, template=None, body=None) -> Optional[str]:
    """Saves feedback along with optional session information in a SQL DB"""
    if template:
      body = template.content

    if interview and (session_id or body):
      stmt = insert(feedback_session_table).values(interview=interview, session_id=session_id, body=body)
      with engine.begin() as conn:
        result = conn.execute(stmt)
        id_for_feedback = result.inserted_primary_key[0]

      return id_for_feedback
    else: # can happen if the forwarding interview didn't pass session info
      return None

def set_feedback_github_url(id_for_feedback:str, github_url:str) -> bool:
    """Returns true if save was successful"""
    stmt = update(feedback_session_table).where(feedback_session_table.c.id == id_for_feedback).values(html_url=github_url)
    with engine.begin() as conn:
      result = conn.execute(stmt)
    if result.rowcount == 0:
      log(f'Cannot find {id_for_feedback} in redis DB')
      return False
    return True

def get_all_feedback_info(interview=None) -> Iterable:
    if interview:
        stmt = select(feedback_session_table).where(feedback_session_table.c.interview == interview)
    else:
        stmt = select(feedback_session_table)
    with engine.begin() as conn:
        results = conn.execute(stmt)
        # Turn into literal dict because DA is too eager to save / load SQLAlchemy objects into the interview SQL
        return {str(row['id']): dict(row) for row in results.mappings()}
