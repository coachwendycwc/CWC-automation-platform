"""Encrypt contractor tax_id (SSN/EIN) at rest

The contractors.tax_id column stored the SSN/EIN in plaintext despite a code
comment claiming it was encrypted. This migration adds tax_id_encrypted,
Fernet-encrypts every existing plaintext value into it, and drops the old
plaintext column. The application reads/writes only through the encrypting
`tax_id` property on the model.

Revision ID: 012
Revises: 011
Create Date: 2026-07-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "011a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    from app.services.field_encryption import encrypt_value

    # Databases built by create_all before the schema was migration-managed
    # already have the encrypted column and may already have lost the plaintext
    # one. Each step is therefore conditional, so this runs cleanly on both a
    # fresh database and a create_all-era one.
    existing = _columns("contractors")

    # 1. Add the ciphertext column (nullable so the add succeeds before backfill).
    if "tax_id_encrypted" not in existing:
        with op.batch_alter_table("contractors") as batch_op:
            batch_op.add_column(
                sa.Column("tax_id_encrypted", sa.String(255), nullable=True)
            )

    if "tax_id" not in existing:
        return  # nothing to migrate: plaintext column is already gone

    # 2. Encrypt existing plaintext values in place.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, tax_id FROM contractors WHERE tax_id IS NOT NULL")
    ).fetchall()
    for row_id, plaintext in rows:
        conn.execute(
            sa.text(
                "UPDATE contractors SET tax_id_encrypted = :ct WHERE id = :id"
            ),
            {"ct": encrypt_value(plaintext), "id": row_id},
        )

    # 3. Drop the plaintext column.
    with op.batch_alter_table("contractors") as batch_op:
        batch_op.drop_column("tax_id")


def downgrade() -> None:
    from app.services.field_encryption import decrypt_value

    with op.batch_alter_table("contractors") as batch_op:
        batch_op.add_column(sa.Column("tax_id", sa.String(20), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, tax_id_encrypted FROM contractors "
            "WHERE tax_id_encrypted IS NOT NULL"
        )
    ).fetchall()
    for row_id, ciphertext in rows:
        conn.execute(
            sa.text("UPDATE contractors SET tax_id = :pt WHERE id = :id"),
            {"pt": decrypt_value(ciphertext), "id": row_id},
        )

    with op.batch_alter_table("contractors") as batch_op:
        batch_op.drop_column("tax_id_encrypted")
