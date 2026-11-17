"""Application FastAPI : python -m uvicorn backend.main:app --reload."""

import os
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from generateur.exercise_generator import EXERCISE_TYPES, generate_exercise

from .schemas import (
    AnswerRequest, Catalog, Correction, Error, Exercise, GenerateRequest, Health,
)
from .store import ExerciseStore


def create_app() -> FastAPI:
    app = FastAPI(
        title="PLP — API d'exercices",
        version="0.1.0",
        description="Génération locale et correction d'exercices. Cache temporaire, sans compte utilisateur.",
    )
    app.state.exercises = ExerciseStore()
    origins = [origin.strip() for origin in os.getenv(
        "PLP_CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware, allow_origins=origins,
        allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
    )

    @app.get("/health", response_model=Health, tags=["Service"], summary="Vérifier le service")
    def health():
        """Renvoie `ok` lorsque le processus répond."""
        return Health()

    @app.get("/api/v1/exercise-types", response_model=Catalog, tags=["Exercices"], summary="Lister les types et niveaux")
    def catalog():
        """Décrit les valeurs acceptées par la génération."""
        return Catalog(types=list(EXERCISE_TYPES), difficultes=[1, 2, 3])

    @app.post("/api/v1/exercises", response_model=Exercise, status_code=201, tags=["Exercices"], summary="Générer un exercice")
    def generate(payload: GenerateRequest, request: Request, response: Response):
        """Génère et conserve un exercice. La bonne réponse reste côté serveur."""
        exercise = generate_exercise(payload.type, payload.difficulty)
        request.app.state.exercises.add(exercise)
        response.headers["Location"] = f"/api/v1/exercises/{exercise['identifiant']}"
        return exercise

    def find(identifier: UUID, request: Request):
        exercise = request.app.state.exercises.get(identifier.hex)
        if exercise is None:
            raise HTTPException(404, "Exercice introuvable ou expiré.")
        return exercise

    @app.get("/api/v1/exercises/{identifier}", response_model=Exercise, responses={404: {"model": Error}}, tags=["Exercices"], summary="Récupérer un exercice")
    def retrieve(identifier: UUID, request: Request):
        """Renvoie l'exercice conservé en mémoire, sans sa réponse."""
        return find(identifier, request)

    @app.post("/api/v1/exercises/{identifier}/answers", response_model=Correction, responses={404: {"model": Error}}, tags=["Exercices"], summary="Corriger une réponse")
    def correct(identifier: UUID, payload: AnswerRequest, request: Request):
        """Compare exactement la réponse soumise et renvoie la solution. Aucun résultat n'est conservé."""
        exercise = find(identifier, request)
        expected = exercise["bonne_reponse"]
        submitted = payload.reponse
        if type(submitted) is not type(expected):
            raise HTTPException(422, "Format de réponse incompatible avec le type d'exercice.")
        return Correction(
            identifiant=exercise["identifiant"],
            correcte=submitted == expected, bonne_reponse=expected,
        )

    return app


app = create_app()
