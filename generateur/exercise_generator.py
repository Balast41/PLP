"""Génération locale d'exercices pédagogiques simples."""

from __future__ import annotations

import random
import uuid
from typing import Any, Callable


EXERCISE_TYPES = ("association", "intrus", "denombrement")

_ASSOCIATIONS = (
    (("chat", "animal"), ("pomme", "fruit"), ("chaise", "meuble"), ("bus", "véhicule"), ("rose", "fleur")),
    (("abeille", "ruche"), ("oiseau", "nid"), ("lapin", "terrier"), ("chien", "niche"), ("poule", "poulailler")),
    (("rouge", "couleur"), ("cercle", "forme"), ("trois", "nombre"), ("été", "saison"), ("Paris", "ville")),
    (("cuillère", "manger"), ("crayon", "dessiner"), ("ballon", "jouer"), ("savon", "laver"), ("lit", "dormir")),
)

_INTRUS = (
    (("pomme", "poire", "banane", "orange", "fraise"), "chaise"),
    (("chat", "chien", "lapin", "cheval", "mouton"), "vélo"),
    (("rouge", "bleu", "vert", "jaune", "violet"), "carré"),
    (("cercle", "carré", "triangle", "rectangle", "ovale"), "fourchette"),
    (("lundi", "mardi", "mercredi", "jeudi", "vendredi"), "hiver"),
    (("courir", "sauter", "marcher", "ramper", "grimper"), "dormir"),
)

_COUNTABLE_ITEMS = ("étoile", "pomme", "ballon", "fleur", "cube")


def _identifier() -> str:
    return uuid.uuid4().hex


def _association(difficulty: int) -> dict[str, Any]:
    pairs = list(random.choice(_ASSOCIATIONS))
    pair_count = min(2 + difficulty, len(pairs))
    pairs = pairs[:pair_count]
    left = [left_item for left_item, _ in pairs]
    right = [right_item for _, right_item in pairs]
    random.shuffle(left)
    random.shuffle(right)
    return {
        "identifiant": _identifier(),
        "type": "association",
        "difficulte": difficulty,
        "enonce": "Associe chaque mot de la première liste à sa catégorie ou à son élément lié.",
        "propositions": {"elements": left, "correspondances": right},
        "bonne_reponse": {left_item: right_item for left_item, right_item in pairs},
    }


def _intrus(difficulty: int) -> dict[str, Any]:
    related, odd_one_out = random.choice(_INTRUS)
    related_count = min(2 + difficulty, len(related))
    choices = list(related[:related_count]) + [odd_one_out]
    random.shuffle(choices)
    return {
        "identifiant": _identifier(),
        "type": "intrus",
        "difficulte": difficulty,
        "enonce": "Trouve le mot qui n'appartient pas à la même famille que les autres.",
        "propositions": choices,
        "bonne_reponse": odd_one_out,
    }


def _denombrement(difficulty: int) -> dict[str, Any]:
    maximum = (5, 10, 20)[difficulty - 1]
    minimum = (1, 4, 8)[difficulty - 1]
    count = random.randint(minimum, maximum)
    item = random.choice(_COUNTABLE_ITEMS)
    distractors = {max(0, count - 2), max(0, count - 1), count + 1, count + 2}
    distractors.discard(count)
    choices = random.sample(sorted(distractors), 3) + [count]
    random.shuffle(choices)
    plural = item if count == 1 else item + "s"
    return {
        "identifiant": _identifier(),
        "type": "denombrement",
        "difficulte": difficulty,
        "enonce": f"Compte les {plural} : " + " | ".join([item] * count),
        "propositions": choices,
        "bonne_reponse": count,
    }


_GENERATORS: dict[str, Callable[[int], dict[str, Any]]] = {
    "association": _association,
    "intrus": _intrus,
    "denombrement": _denombrement,
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
