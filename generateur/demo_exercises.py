"""Démonstration et validation légère du générateur d'exercices."""

import json

from exercise_generator import EXERCISE_TYPES, generate_exercise


REQUIRED_FIELDS = {
    "identifiant",
    "type",
    "difficulte",
    "enonce",
    "propositions",
    "bonne_reponse",
}


def validate(exercise: dict) -> None:
    """Lève une AssertionError si la structure minimale est invalide."""
    assert set(exercise) == REQUIRED_FIELDS
    assert isinstance(exercise["identifiant"], str) and exercise["identifiant"]
    assert exercise["type"] in EXERCISE_TYPES
    assert exercise["difficulte"] in (1, 2, 3)
    assert isinstance(exercise["enonce"], str) and exercise["enonce"]
    assert exercise["propositions"]
    choices = exercise["propositions"]
    answer = exercise["bonne_reponse"]
    if exercise["type"] == "association":
        assert set(answer) == set(choices["elements"])
        assert set(answer.values()) == set(choices["correspondances"])
        assert len(answer) == 2 + exercise["difficulte"]
    else:
        assert len(choices) == len(set(choices))
        assert choices.count(answer) == 1
        if exercise["type"] == "denombrement":
            assert all(isinstance(choice, int) and choice >= 0 for choice in choices)
            assert len(exercise["enonce"].split(": ", 1)[1].split(" | ")) == answer
    json.dumps(exercise, ensure_ascii=False)


def main() -> None:
    requested_types = ("association", "intrus", "denombrement", None, None)
    exercises = [
        generate_exercise(exercise_type, difficulty=index % 3 + 1)
        for index, exercise_type in enumerate(requested_types)
    ]
    for exercise in exercises:
        validate(exercise)
    assert len({exercise["identifiant"] for exercise in exercises}) == 5

    print(json.dumps(exercises, ensure_ascii=False, indent=2))
    print("\n5 exercices valides générés.")


if __name__ == "__main__":
    main()
