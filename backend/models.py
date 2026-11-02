from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Index, func,
    text as sql_text,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import UserDefinedType

from envutil import env_int as _env_int

_DIALECT = {"name": "postgresql"}


def configure_dialect(name: str) -> None:
    _DIALECT["name"] = name


EMBED_DIM = _env_int("EMBED_DIM", 384, 64, 4096)


EMBED_COL = f"embedding_{EMBED_DIM}"


class pgvector_type(UserDefinedType):
    def __init__(self, dim: int = None):
        dim = EMBED_DIM if dim is None else dim
        self.dim = dim

    def get_col_spec(self, **kw):
        if _DIALECT["name"] == "sqlite":
            return "TEXT"
        return f"vector({self.dim})"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return "[" + ",".join(str(f) for f in value) + "]"
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, list):
                return value
            clean = value.strip("[]").strip()
            if not clean:
                return []
            return [float(x) for x in clean.split(",") if x.strip()]
        return process


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_suspended = Column(Boolean, nullable=False, default=False)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    token_version = Column(Integer, nullable=False, default=0)
    state_code = Column(String(4), nullable=True)
    code_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    nickname = Column(String(50), nullable=True)

    reset_token = Column(String(80), nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    reset_attempts = Column(Integer, nullable=False, default=0)

    email_verified = Column(Boolean, nullable=False, default=True, server_default=sql_text("true"))

    last_login_ip = Column(String(80), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    totp_secret = Column(Text, nullable=True)
    totp_enabled = Column(Boolean, nullable=False, default=False)

    consent_given = Column(Boolean, nullable=False, default=False)
    consent_updated_at = Column(DateTime(timezone=True), nullable=True)

    terms_version = Column(String(50), nullable=True)
    privacy_version = Column(String(50), nullable=True)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    forum_nickname = Column(String(50), nullable=True, unique=True)
    forum_avatar = Column(String(10), nullable=True)
    profile_memory_enabled = Column(Boolean, nullable=False, default=False, server_default=sql_text("false"))


class StateCode(Base):
    __tablename__ = "state_codes"
    code = Column(String(4), primary_key=True)
    a = Column(Integer, nullable=False)
    p = Column(Integer, nullable=False)
    h = Column(Integer, nullable=False)
    c = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    severity = Column(String(50), nullable=False, default="")
    profile = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String(40), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(40), ForeignKey("quiz_submissions.id", ondelete="SET NULL"), nullable=True, index=True)
    state_code = Column(String(4), nullable=True, index=True)
    role = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    id = Column(String(40), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    norms = Column(JSON, nullable=False)
    code = Column(String(4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserGoal(Base):
    __tablename__ = "user_goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(40), ForeignKey("quiz_submissions.id", ondelete="SET NULL"), nullable=True, index=True)
    scale = Column(String(1), nullable=False, default="")
    text = Column(String(300), nullable=False)
    status = Column(String(12), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False, default="")
    source_messages = Column(Integer, nullable=False, default=0)
    source_sessions = Column(Integer, nullable=False, default=0)
    model_name = Column(String(120), nullable=False, default="")
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String(60), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(260), nullable=False, index=True)
    source_path = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    title = Column(String(260), nullable=False, default="")
    content = Column(Text, nullable=False)
    embedding = Column(EMBED_COL, pgvector_type(EMBED_DIM), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    purpose = Column(String(32), nullable=False, default="login")
    attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_hash = Column(String(128), unique=True, nullable=False, index=True)
    label = Column(String(160), nullable=False, default="Megbízható eszköz")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(120), nullable=False)
    detail = Column(Text, nullable=False, default="")
    ip = Column(String(80), nullable=False, default="")
    user_agent = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    source = Column(String(20), nullable=False, default="watch")
    kind = Column(String(40), nullable=False, default="")
    severity = Column(String(20), nullable=False, default="info")
    label = Column(String(200), nullable=False, default="")
    detail = Column(Text, nullable=False, default="")
    quarantined = Column(Boolean, nullable=False, default=False)


class GameSession(Base):
    __tablename__ = "game_sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_type = Column(String(16), nullable=False)
    challenge = Column(JSON, nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True))


class CrisisNotification(Base):
    __tablename__ = "crisis_notification_outbox"
    id = Column(String(40), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, index=True)


class UsedRefreshToken(Base):
    __tablename__ = "used_refresh_tokens"
    jti = Column(String(64), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"
    __table_args__ = (Index("ux_leaderboard_user_game", "user_id", "game_type", unique=True),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_type = Column(String(40), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
