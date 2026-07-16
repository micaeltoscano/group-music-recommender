"""Testes independentes do QA para o PB-05 (entrada e lobby).

Estes testes são de autoria do Agente de Teste (QA), separados dos testes do
implementador (`test_pb05_rooms.py`). Objetivo: validar de forma adversarial o
limite sob concorrência real no PostgreSQL, a idempotência e a autorização —
sem confiar no relato do Dev.

Requer `TEST_DATABASE_URL` apontando para um PostgreSQL isolado já migrado.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.models import MusicSessionMember, User
from app.services import room_service

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL não configurada para os testes de QA no PostgreSQL.",
)


@pytest.fixture()
def factory():
    engine = create_engine(os.environ["TEST_DATABASE_URL"], future=True)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    engine.dispose()


def _seed(factory, n_users: int):
    """Cria n usuários e uma sala com o primeiro como host. Devolve (ids, code)."""
    db = factory()
    try:
        run_id = uuid4().hex
        users = [
            User(spotify_id=f"qa_pb05_{run_id}_{i}", display_name=f"QA User {i}")
            for i in range(n_users)
        ]
        db.add_all(users)
        db.flush()
        ids = [u.id for u in users]
        room, _ = room_service.create_room(db, ids[0])
        return ids, room.code, room.id
    finally:
        db.close()


def _cleanup(factory, ids):
    db = factory()
    try:
        db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _count_members(factory, room_id) -> int:
    db = factory()
    try:
        return db.scalar(
            select(room_service.func.count())
            .select_from(MusicSessionMember)
            .where(MusicSessionMember.session_id == room_id)
        )
    finally:
        db.close()


def test_qa_pb05_heavy_contention_never_exceeds_five(factory):
    """20 usuários distintos disputando 4 vagas: exatamente 4 entram, total = 5."""
    ids, code, room_id = _seed(factory, 21)  # 1 host + 20 candidatos
    try:
        def join_one(user_id: int) -> str:
            db = factory()
            try:
                room_service.join_room(db, code, user_id)
                return "joined"
            except room_service.RoomFullError:
                return "full"
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=20) as ex:
            results = list(ex.map(join_one, ids[1:]))

        assert results.count("joined") == 4, f"esperado 4 ingressos, obtido {results.count('joined')}"
        assert results.count("full") == 16
        assert _count_members(factory, room_id) == 5
    finally:
        _cleanup(factory, ids)


def test_qa_pb05_concurrent_duplicate_join_creates_single_membership(factory):
    """O MESMO usuário fazendo join 10x em paralelo gera um único vínculo."""
    ids, code, room_id = _seed(factory, 2)
    try:
        guest = ids[1]

        def join_same(_) -> int:
            db = factory()
            try:
                room_service.join_room(db, code, guest)
                return 200
            except room_service.RoomFullError:
                return 409
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=10) as ex:
            statuses = list(ex.map(join_same, range(10)))

        assert set(statuses) == {200}, f"join idempotente deveria sempre responder 200: {statuses}"
        db = factory()
        try:
            assert (
                db.query(MusicSessionMember)
                .filter(
                    MusicSessionMember.session_id == room_id,
                    MusicSessionMember.user_id == guest,
                )
                .count()
                == 1
            )
        finally:
            db.close()
        assert _count_members(factory, room_id) == 2  # host + convidado
    finally:
        _cleanup(factory, ids)


def test_qa_pb05_expired_room_rejects_join_at_exact_boundary(factory):
    """Sala exatamente no instante de expiração é rejeitada (limite <=)."""
    ids, _, _ = _seed(factory, 2)
    try:
        db = factory()
        try:
            past = datetime.now(timezone.utc) - timedelta(hours=24)
            expired, _ = room_service.create_room(db, ids[0], now=past)
            expired_code = expired.code
            expired_id = expired.id
        finally:
            db.close()

        db = factory()
        try:
            with pytest.raises(room_service.RoomExpiredError):
                room_service.join_room(db, expired_code, ids[1])
        finally:
            db.close()

        # nenhum vínculo criado para o convidado
        db = factory()
        try:
            assert (
                db.query(MusicSessionMember)
                .filter(
                    MusicSessionMember.session_id == expired_id,
                    MusicSessionMember.user_id == ids[1],
                )
                .count()
                == 0
            )
        finally:
            db.close()
    finally:
        _cleanup(factory, ids)


def test_qa_pb05_non_member_cannot_read_room(factory):
    """Não-membro recebe RoomAccessDeniedError e não obtém a sala."""
    ids, code, _ = _seed(factory, 2)
    try:
        db = factory()
        try:
            with pytest.raises(room_service.RoomAccessDeniedError):
                room_service.get_room_for_member(db, code, ids[1])
        finally:
            db.close()
    finally:
        _cleanup(factory, ids)


def test_qa_pb05_unknown_code_is_not_found(factory):
    """Código inexistente levanta RoomNotFoundError (sem vazar existência)."""
    db = factory()
    try:
        with pytest.raises(room_service.RoomNotFoundError):
            room_service.get_room_for_member(db, "ZZZZ-ZZZZ", 1)
    finally:
        db.close()
