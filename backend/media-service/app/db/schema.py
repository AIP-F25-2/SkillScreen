from sqlalchemy import (
    Table, Column, Integer, String, Text, JSON, DateTime,
    ARRAY, MetaData, func, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

media = Table(
    "media_files",
    metadata,

    # --- Primary key ---
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),

    # --- Foreign linkage ---
    Column("interview_id", UUID(as_uuid=False), nullable=False, index=True),
    Column("session_id", UUID(as_uuid=False), nullable=True, index=True),

    # --- File info ---
    Column("file_type", String(50), nullable=False),          # e.g. 'video', 'resume', 'interview', 'file'
    Column("storage_uri", Text, nullable=True),                # full Azure or local path
    Column("file_size", BigInteger, nullable=True),
    Column("duration", Integer, nullable=True),
    Column("mime_type", String(255), nullable=True),
    Column("checksum", String(255), nullable=True),

    # --- Upload progress tracking ---
    Column("expected_total", Integer, nullable=True),
    Column("received_indices", ARRAY(Integer), nullable=True),
    Column("status", String(50), nullable=True, index=True),   # 'uploading', 'completed', 'aborted', etc.

    # --- Flexible metadata ---
    Column("metadata", JSON, nullable=True),

    # --- Timestamps ---
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
)

# Example SQL equivalent:
# CREATE TABLE public.media_files (
#   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
#   interview_id uuid NOT NULL,
#   session_id uuid NULL,
#   file_type varchar(50) NOT NULL,
#   storage_uri text,
#   file_size bigint,
#   duration int,
#   mime_type varchar(255),
#   checksum varchar(255),
#   expected_total int,
#   received_indices int[],
#   status varchar(50),
#   metadata jsonb,
#   created_at timestamptz DEFAULT now(),
#   updated_at timestamptz DEFAULT now(),
#   deleted_at timestamptz
# );
