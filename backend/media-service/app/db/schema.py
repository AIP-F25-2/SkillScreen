# app/db/schema.py
from sqlalchemy import (
    Table, Column, Integer, String, Text, JSON, DateTime,
    ARRAY, MetaData, func
)

metadata = MetaData()

media = Table(
    "media",
    metadata,

    # Primary key
    Column("id", Integer, primary_key=True),

    # --- Ownership / linkage ---
    Column("user_id", String(100), nullable=True, index=True),          # uploader or assigned user
    Column("assigned_user", String(100), nullable=True, index=True),    # optional (for HR/interviewer)
    Column("candidate_id", String(100), nullable=True, index=True),
    Column("interview_id", String(100), nullable=True, index=True),
    Column("session_id", String(100), nullable=True, index=True),

    # --- File / content info ---
    Column("media_type", String(50), nullable=False),                   # 'resume', 'interview', 'video', 'file', 'session', etc.
    Column("file_path", Text, nullable=True),                           # blob virtual path (e.g. "videos/user123/file.mp4")
    Column("blob_name", Text, nullable=True),                           # Azure blob reference if needed
    Column("content_type", Text, nullable=True),
    Column("status", String(50), nullable=True),                        # 'uploaded', 'active', 'finalized', etc.

    # --- Meta data ---
    Column("size_bytes", Integer, nullable=True),
    Column("duration_ms", Integer, nullable=True),
    Column("expected_total", Integer, nullable=True),                   # for chunked uploads
    Column("received_indices", ARRAY(Integer), nullable=True),          # stores list of received chunks
    Column("extra", JSON, nullable=True),                               # flexible JSON field for misc data

    # --- Timestamps ---
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)



# CREATE TABLE media (
#   id serial PRIMARY KEY,
#   user_id varchar(128),
#   media_type varchar(64) NOT NULL,
#   file_path text,
#   blob_name text,
#   content_type text,
#   session_id varchar(128),
#   expected_total int,
#   received_indices int[],
#   status varchar(32),
#   candidate_id varchar(128),
#   interview_id varchar(128),
#   assigned_user varchar(128),
#   size_bytes int,
#   duration_ms int,
#   extra jsonb NOT NULL DEFAULT '{}'::jsonb,
#   created_at timestamptz NOT NULL DEFAULT now(),
#   updated_at timestamptz NOT NULL DEFAULT now()
# );
# CREATE INDEX ix_media_user_id ON media(user_id);
# CREATE INDEX ix_media_session_id ON media(session_id);
# CREATE INDEX ix_media_candidate_id ON media(candidate_id);
# CREATE INDEX ix_media_interview_id ON media(interview_id);
