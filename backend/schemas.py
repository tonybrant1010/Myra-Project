from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from envutil import env_int as _env_int


CHAT_MESSAGE_MAX_CHARS = _env_int("CHAT_MESSAGE_MAX_CHARS", 8000, 500, 20000)


class RegisterBody(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    accepted_terms: bool = False
    accepted_terms_version: Optional[str] = Field(default=None, max_length=40)
    accepted_privacy_version: Optional[str] = Field(default=None, max_length=40)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    device_token: Optional[str] = Field(None, max_length=128)


class NicknameBody(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)


class GameSessionStartBody(BaseModel):
    game_type: Literal["match", "snake", "sudoku"]
    board_size: Literal[4, 6, 9] = 4


class SubmitScoreBody(BaseModel):
    game_type: Literal["match", "snake", "sudoku"]
    score: int = Field(ge=0, le=1000000)
    session_token: str = Field(min_length=16, max_length=128)
    game_proof: dict = Field(default_factory=dict)


class MfaVerifyBody(BaseModel):
    challenge_id: str = Field(min_length=8, max_length=80)
    code: str = Field(min_length=4, max_length=12)
    remember_device: bool = False


class MfaSettingsBody(BaseModel):
    enabled: bool
    current_password: str = Field(min_length=1, max_length=128)


class MfaTrustedDeviceDeleteBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class DeleteAccountBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class EmailOnlyBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    email: EmailStr
    token: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    admin_security_challenge_id: Optional[str] = Field(None, max_length=80)
    admin_security_code: Optional[str] = Field(None, max_length=16)


class CodeVerifyBody(BaseModel):
    code: str = Field(min_length=1, max_length=16)


class QuizSubmitBody(BaseModel):
    answers: List[int]

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v):
        if len(v) != 21:
            raise ValueError("Exactly 21 answers required")
        for idx in range(16):
            if not (1 <= v[idx] <= 5):
                raise ValueError(f"First 16 answers must be between 1 and 5 (got {v[idx]} at index {idx})")
        for idx in range(16, 21):
            if not (0 <= v[idx] <= 2):
                raise ValueError(f"Last 5 answers must be between 0 and 2 (got {v[idx]} at index {idx})")
        return v


class ChatSendBody(BaseModel):
    message: str = Field(min_length=1, max_length=CHAT_MESSAGE_MAX_CHARS)
    session_id: Optional[str] = Field(None, max_length=40)


class GoalItemIn(BaseModel):
    text: str = Field(min_length=3, max_length=300)
    scale: str = Field("", max_length=1)

    @field_validator("scale")
    @classmethod
    def _valid_scale(cls, v: str) -> str:
        v = (v or "").lower().strip()
        if v and v not in ("a", "p", "h", "c"):
            raise ValueError("Érvénytelen skála.")
        return v


class GoalsCreateBody(BaseModel):
    items: List[GoalItemIn] = Field(min_length=1, max_length=3)


class StateCodeIn(BaseModel):
    code: str = Field(min_length=1, max_length=4)
    title: str = Field(min_length=1, max_length=240)
    profile: str
    severity: str = Field("", max_length=80)
    a: Optional[int] = Field(None, ge=1, le=4)
    p: Optional[int] = Field(None, ge=1, le=4)
    h: Optional[int] = Field(None, ge=1, le=4)
    c: Optional[int] = Field(None, ge=1, le=4)


class SettingsIn(BaseModel):
    llm_provider: Optional[Literal["openai", "anthropic", "gemini", "groq", "cerebras", "mistral", "openrouter", "dashscope", "ollama"]] = None
    llm_model: Optional[str] = Field(None, max_length=160)
    llm_api_key: Optional[str] = None
    system_prompt: Optional[str] = None
    kb_text: Optional[str] = None
    global_notice_text: Optional[str] = Field(None, max_length=1200)
    profile_memory_enabled: Optional[bool] = None
    local_llm_enabled: Optional[bool] = None
    local_llm_model: Optional[str] = Field(None, max_length=160)
    local_llm_temperature: Optional[str] = Field(None, max_length=12)
    local_llm_top_p: Optional[str] = Field(None, max_length=12)
    local_llm_top_k: Optional[str] = Field(None, max_length=12)
    local_llm_min_p: Optional[str] = Field(None, max_length=12)
    local_llm_thinking: Optional[str] = Field(None, max_length=8)


class ReindexPdfKnowledgeBody(BaseModel):
    source_dir: Optional[str] = Field(None, max_length=500)


class TotpVerifySetupBody(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class TotpDisableBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=6)


class RefreshTokenBody(BaseModel):
    refresh_token: str


class ConsentBody(BaseModel):
    consent_given: bool


class ExportDataBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class FeedbackBody(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    context: str = Field("", max_length=40)


class TtsSpeakBody(BaseModel):
    text: str = Field(min_length=1, max_length=2500)


class TotpLoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=6)


class ProfileMemoryBody(BaseModel):
    enabled: bool


class MaintenanceModeBody(BaseModel):
    maintenance_mode: bool
    current_password: str = Field(min_length=1, max_length=128)


class EmergencyAdminActionBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class SecurityActionBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    reason: str = Field(default="", max_length=200)


class ForumProfileUpdate(BaseModel):
    nickname: str
    avatar: str = Field(max_length=10)


class ForumPostCreate(BaseModel):
    content: str
