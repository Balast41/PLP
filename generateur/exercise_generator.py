"""Génération locale d'exercices pédagogiques simples."""

from __future__ import annotations

import json
import random
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


EXERCISE_TYPES = ("association", "intrus", "denombrement")

_DATA_DIRECTORY = Path(__file__).resolve().parent / "donnees"

@lru_cache(maxsize=len(EXERCISE_TYPES))
def _load_template(exercise_type: str) -> dict[str, Any]:
    """Charge le catalogue local une fois par type et par processus."""
    path = _DATA_DIRECTORY / f"{exercise_type}.json"
    try:
        with path.open(encoding="utf-8") as source:
            template = json.load(source)
    except (OSError, ValueError) as error:
        raise ValueError(f"Impossible de charger le catalogue {path.name} : {error}") from error
    if (
        not isinstance(template, dict)
        or template.get("version") != 1
        or template.get("type") != exercise_type
        or not isinstance(template.get("enonce"), str)
        or not template["enonce"].strip()
        or not isinstance(template.get("modeles"), list)
        or not template["modeles"]
        or not isinstance(template.get("difficultes"), dict)
        or set(template["difficultes"]) != {"1", "2", "3"}
    ):
        raise ValueError(f"Structure de catalogue invalide : {path.name}")
    return template


def _identifier() -> str:
    return uuid.uuid4().hex


def _association(difficulty: int) -> dict[str, Any]:
    template = _load_template("association")
    pairs = list(random.choice(template["modeles"])["paires"])
    pair_count = template["difficultes"][str(difficulty)]["nombre_paires"]
    pairs = pairs[:pair_count]
    left = [left_item for left_item, _ in pairs]
    right = [right_item for _, right_item in pairs]
    random.shuffle(left)
    random.shuffle(right)
    return {
        "identifiant": _identifier(),
        "type": "association",
        "difficulte": difficulty,
        "enonce": template["enonce"],
        "propositions": {"elements": left, "correspondances": right},
        "bonne_reponse": {left_item: right_item for left_item, right_item in pairs},
    }


def _intrus(difficulty: int) -> dict[str, Any]:
    template = _load_template("intrus")
    model = random.choice(template["modeles"])
    related, odd_one_out = model["elements"], model["intrus"]
    related_count = template["difficultes"][str(difficulty)]["nombre_elements"]
    choices = list(related[:related_count]) + [odd_one_out]
    random.shuffle(choices)
    return {
        "identifiant": _identifier(),
        "type": "intrus",
        "difficulte": difficulty,
        "enonce": template["enonce"],
        "propositions": choices,
        "bonne_reponse": odd_one_out,
    }


def _denombrement(difficulty: int) -> dict[str, Any]:
    template = _load_template("denombrement")
    level = template["difficultes"][str(difficulty)]
    maximum, minimum = level["maximum"], level["minimum"]
    count = random.randint(minimum, maximum)
    model = random.choice(template["modeles"])
    item = model["element"]
    distractors = {max(0, count - 2), max(0, count - 1), count + 1, count + 2}
    distractors.discard(count)
    choices = random.sample(sorted(distractors), 3) + [count]
    random.shuffle(choices)
    plural = item if count == 1 else model["pluriel"]
    return {
        "identifiant": _identifier(),
        "type": "denombrement",
        "difficulte": difficulty,
        "enonce": template["enonce"].format(nom=plural, elements=" | ".join([item] * count)),
        "propositions": choices,
        "bonne_reponse": count,
    }


def _memory(difficulty: int) -> dict[str, Any]:
    template = _load_template("memory")
    level = template["difficultes"][str(difficulty)]
    pair_count = level["nombre_paires"]
    pairs = list(random.choice(template["modeles"])["paires"])
    pairs = pairs[:pair_count]
    left = [left_item for left_item, _ in pairs]
    right = [right_item for _, right_item in pairs]
    random.shuffle(left)
    random.shuffle(right)
    return {
        "identifiant": _identifier(),
        "type": "memory",
        "difficulte": difficulty,
        "enonce": template["enonce"],
        "propositions": {"elements": left, "correspondances": right},
        "bonne_reponse": {left_item: right_item for left_item, right_item in pairs},
    }

_GENERATORS: dict[str, Callable[[int], dict[str, Any]]] = {
    "association": _association,
    "intrus": _intrus,
    "denombrement": _denombrement,
    "memory": _memory,
}


def generate_exercise(type: str | None = None, difficulty: int = 1) -> dict[str, Any]:
    """Retourne un exercice JSON-sérialisable.

    ``type`` peut valoir ``association``, ``intrus`` ou ``denombrement``.
    Lorsqu'il est omis, un type est choisi aléatoirement. La difficulté va de 1 à 3.
    """
    if type is not None and type not in _GENERATORS:
        raise ValueError(f"Type inconnu : {type!r}. Types disponibles : {', '.join(EXERCISE_TYPES)}")
    if not isinstance(difficulty, int) or isinstance(difficulty, bool) or difficulty not in (1, 2, 3):
        raise ValueError("La difficulté doit être un entier compris entre 1 et 3.")

    exercise_type = type or random.choice(EXERCISE_TYPES)
    return _GENERATORS[exercise_type](difficulty)
