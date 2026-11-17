"""Validation des comptes, profils, séances et administration."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .schemas import AnswerRequest, Difficulty, Exercise, ExerciseType

Role = Literal['child', 'teacher', 'parent', 'support']
Skill = Literal['vocabulaire', 'categorisation', 'numeration']
Assistance = Literal['total', 'partiel', 'allege', 'autonome']
Password = Annotated[str, Field(min_length=12, max_length=128)]
Name = Annotated[str, Field(min_length=1, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)


class EmailInput(Input):
    email: str = Field(max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class Register(EmailInput):
    username: Name
    password: Password
    role: Role


class Login(EmailInput):
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(Input):
    username: Name


class PasswordChange(Input):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password


class LearnerCreate(Input):
    name: Name
    audio: bool = False


class CurriculumUpdate(Input):
    skills: list[Skill] = Field(min_length=1, max_length=3)

    @field_validator('skills')
    @classmethod
    def unique(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('Compétences en double.')
        return value


class Invitation(EmailInput):
    pass


class InvitationAccept(Input):
    token: str = Field(min_length=20, max_length=200)


class SessionCreate(Input):
    mode: Literal['initial', 'evaluated', 'practice'] = 'evaluated'
    type: ExerciseType | None = None
    difficulty: Difficulty | None = None
    count: int = Field(default=5, ge=3, le=20, strict=True)


class Submission(AnswerRequest):
    elapsed_seconds: float = Field(default=0, ge=0, le=86400, allow_inf_nan=False)


class Completion(Input):
    assistance: Assistance
    notes: str = Field(default='', max_length=2000)


class AccountStatus(Input):
    active: bool


class AccountRole(Input):
    role: Role


class UserView(BaseModel):
    id: str
    username: str
    email: str
    role: Literal['child', 'teacher', 'parent', 'support', 'admin']
    active: bool
    created_at: float


class TokenView(BaseModel):
    access_token: str
    token_type: Literal['bearer']
    expires_in: int
    user: UserView


class LearnerView(BaseModel):
    id: str
    name: str
    owner_id: str
    audio: bool
    created_at: float


class SkillView(BaseModel):
    id: Skill
    exercise_type: ExerciseType


class CurriculumView(BaseModel):
    skills: list[Skill]


class InvitationView(BaseModel):
    token: str
    expires_at: float


class LinkView(BaseModel):
    learner_id: str


class SessionSummary(BaseModel):
    id: str
    learner_id: str
    created_by: str
    mode: Literal['initial', 'evaluated', 'practice']
    status: Literal['open', 'completed', 'cancelled']
    created_at: float
    completed_at: float | None
    assistance: Assistance | None
    notes: str


class SessionExercise(Exercise):
    skill: Skill
    answered: bool


class SessionView(SessionSummary):
    exercices: list[SessionExercise]


class CancellationView(BaseModel):
    id: str
    status: Literal['cancelled']


class RuleView(BaseModel):
    reussite: str
    autonomie: str
    activation: float
    conclusion: float


class InferenceView(BaseModel):
    score: float
    appartenances_reussite: dict[str, float]
    appartenances_autonomie: dict[str, float]
    regles: list[RuleView]


class ProgressView(BaseModel):
    etat: Literal['non_evalue', 'non_validee', 'en_apprentissage', 'a_confirmer', 'validee']
    score: float | None
    seances: int
    confirmations: int
    difficulty: int
    inference: InferenceView | None


class ActivityView(ProgressView):
    skill: Skill
    type: ExerciseType


class RecommendationView(BaseModel):
    initial_assessment_required: bool
    activities: list[ActivityView]
