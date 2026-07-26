"""Tax ID (SSN/EIN) encryption-at-rest and masking."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contractor import Contractor
from app.services.field_encryption import (
    decrypt_value,
    encrypt_value,
    mask_tax_id,
)


class TestFieldEncryptionService:
    def test_encrypt_then_decrypt_round_trips(self):
        ct = encrypt_value("12-3456789")
        assert ct is not None
        assert ct != "12-3456789"  # not plaintext
        assert decrypt_value(ct) == "12-3456789"

    def test_none_and_empty_pass_through(self):
        assert encrypt_value(None) is None
        assert encrypt_value("") is None
        assert decrypt_value(None) is None

    def test_ciphertext_is_not_deterministic(self):
        # Fernet embeds a random IV/timestamp, so equal plaintext -> distinct ct.
        assert encrypt_value("999-88-7777") != encrypt_value("999-88-7777")

    def test_tampered_ciphertext_raises(self):
        with pytest.raises(ValueError):
            decrypt_value("not-valid-fernet-token")

    def test_mask_exposes_only_last_four(self):
        assert mask_tax_id("12-3456789") == "•••••6789"
        assert mask_tax_id(None) is None


class TestProductionFailsClosed:
    def test_production_rejects_default_encryption_key(self, monkeypatch):
        import app.config as config

        config.get_settings.cache_clear()
        monkeypatch.setenv("ENVIRONMENT", "production")
        # A real SECRET_KEY so we isolate the tax-id-key guard specifically.
        monkeypatch.setenv("SECRET_KEY", "a-real-production-secret-key-value")
        monkeypatch.setenv(
            "TAX_ID_ENCRYPTION_KEY", config.DEFAULT_TAX_ID_ENCRYPTION_KEY
        )
        try:
            with pytest.raises(RuntimeError, match="TAX_ID_ENCRYPTION_KEY"):
                config.get_settings()
        finally:
            # Never let a poisoned settings cache leak into other tests.
            config.get_settings.cache_clear()


class TestContractorModelEncryption:
    @pytest.mark.asyncio
    async def test_column_stores_ciphertext_not_plaintext(
        self, db_session: AsyncSession, test_contractor: Contractor
    ):
        # Read the raw column straight from the DB.
        row = (
            await db_session.execute(
                select(Contractor.tax_id_encrypted).where(
                    Contractor.id == test_contractor.id
                )
            )
        ).scalar_one()
        assert row is not None
        assert "12-3456789" not in row  # the plaintext must never touch the DB
        # The property decrypts it back.
        assert test_contractor.tax_id == "12-3456789"
        assert test_contractor.tax_id_masked == "•••••6789"


class TestContractorApiMasksTaxId:
    @pytest.mark.asyncio
    async def test_list_returns_masked_only(
        self, client: AsyncClient, auth_headers, test_contractor: Contractor
    ):
        resp = await client.get("/api/contractors", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.text
        assert "12-3456789" not in body  # full SSN/EIN never serialized
        item = resp.json()["items"][0]
        assert item["tax_id_masked"] == "•••••6789"
        assert "tax_id" not in item  # write-only field absent from reads

    @pytest.mark.asyncio
    async def test_detail_returns_masked_only(
        self, client: AsyncClient, auth_headers, test_contractor: Contractor
    ):
        resp = await client.get(
            f"/api/contractors/{test_contractor.id}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "12-3456789" not in resp.text
        assert resp.json()["tax_id_masked"] == "•••••6789"

    @pytest.mark.asyncio
    async def test_create_encrypts_and_masks(
        self, client: AsyncClient, auth_headers, db_session: AsyncSession
    ):
        resp = await client.post(
            "/api/contractors",
            headers=auth_headers,
            json={"name": "New Co", "tax_id": "55-1112222", "tax_id_type": "ein"},
        )
        assert resp.status_code == 200
        assert resp.json()["tax_id_masked"] == "•••••2222"
        assert "55-1112222" not in resp.text
        # And it is encrypted at rest.
        cid = resp.json()["id"]
        raw = (
            await db_session.execute(
                select(Contractor.tax_id_encrypted).where(Contractor.id == cid)
            )
        ).scalar_one()
        assert "55-1112222" not in raw
