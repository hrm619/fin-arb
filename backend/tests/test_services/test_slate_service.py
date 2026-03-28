"""Tests for slate service."""

from datetime import date

import pytest

from backend.schemas.slate import SlateCreate, SlateUpdate
from backend.services.slate_service import (
    create_slate,
    delete_slate,
    get_slate,
    list_slates,
    update_slate,
)


def _make_slate(db, name="NFL Week 14"):
    return create_slate(
        db, SlateCreate(name=name, week_start=date(2025, 12, 1), week_end=date(2025, 12, 7))
    )


class TestCreateSlate:
    def test_creates_successfully(self, db):
        slate = _make_slate(db)
        assert slate.id is not None
        assert slate.name == "NFL Week 14"

    def test_fields_persisted(self, db):
        slate = _make_slate(db)
        fetched = get_slate(db, slate.id)
        assert fetched.week_start == date(2025, 12, 1)
        assert fetched.week_end == date(2025, 12, 7)


class TestGetSlate:
    def test_returns_slate(self, db):
        slate = _make_slate(db)
        assert get_slate(db, slate.id).name == "NFL Week 14"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError, match="not found"):
            get_slate(db, 999)


class TestListSlates:
    def test_empty(self, db):
        assert list_slates(db) == []

    def test_returns_all(self, db):
        _make_slate(db, "Week 1")
        _make_slate(db, "Week 2")
        assert len(list_slates(db)) == 2


class TestUpdateSlate:
    def test_updates_name(self, db):
        slate = _make_slate(db)
        updated = update_slate(db, slate.id, SlateUpdate(name="NBA Week 1"))
        assert updated.name == "NBA Week 1"

    def test_partial_update(self, db):
        slate = _make_slate(db)
        updated = update_slate(db, slate.id, SlateUpdate(week_start=date(2025, 12, 2)))
        assert updated.week_start == date(2025, 12, 2)
        assert updated.name == "NFL Week 14"

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError):
            update_slate(db, 999, SlateUpdate(name="x"))


class TestDeleteSlate:
    def test_deletes(self, db):
        slate = _make_slate(db)
        assert delete_slate(db, slate.id) is True
        with pytest.raises(ValueError):
            get_slate(db, slate.id)

    def test_raises_on_missing(self, db):
        with pytest.raises(ValueError):
            delete_slate(db, 999)
