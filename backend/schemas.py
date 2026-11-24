"""Contrats JSON publics de l'API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

ExerciseType = Literal["association", "intrus", "denombrement"]
Difficulty = Annotated[int, Field(strict=True, ge=1, le=3)]
Answer = StrictStr | StrictInt | dict[str, StrictStr]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: ExerciseType | None = Field(default=None, description="Type aléatoire si omis ou null.")
    difficulty: Difficulty = Field(default=1, description="Niveau de 1 à 3.")


class Associations(BaseModel):
    elements: list[str]
    correspondances: list[str]


class Exercise(BaseModel):
    identifiant: str
    type: ExerciseType
    difficulte: Difficulty
    enonce: str
    propositions: Associations | list[str] | list[int]


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reponse: Answer = Field(description="Mot intrus, entier compté ou dictionnaire des associations.")


class Correction(BaseModel):
    identifiant: str
    correcte: bool
    bonne_reponse: Answer


class PairAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gauche: StrictStr = Field(description="Élément de gauche proposé.")
    droite: StrictStr = Field(description="Correspondance proposée.")


class PairCorrection(BaseModel):
    identifiant: str
    correcte: bool


class Catalog(BaseModel):
    types: list[ExerciseType]
    difficultes: list[int]


class Health(BaseModel):
    status: Literal["ok"] = "ok"


class Error(BaseModel):
    detail: str
