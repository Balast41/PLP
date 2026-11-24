# Générateur minimal d'exercices

Module autonome Python 3.10 ou supérieur, sans dépendance externe.
Depuis la racine du dépôt :

```sh
python generateur/demo_exercises.py
```

La démonstration affiche cinq exercices et vérifie leur structure, leur
sérialisation JSON et la cohérence des réponses avec les propositions.

```python
from generateur.exercise_generator import generate_exercise

exercise = generate_exercise(type="association", difficulty=1)
```

Types : `association`, `intrus`, `denombrement`. Sans type, le choix est
aléatoire. Difficultés : entiers de 1 à 3. Champs retournés : `identifiant`,
`type`, `difficulte`, `enonce`, `propositions`, `bonne_reponse`.

Les données, les énoncés et les niveaux sont stockés dans les fichiers JSON du
dossier [`donnees/`](donnees/README.md), à raison d'un fichier par type. Pour
modifier le catalogue, éditer ces fichiers puis redémarrer le serveur : les
données sont mises en cache par processus. Les chemins ne dépendent pas du
répertoire de lancement. Le contrat de `generate_exercise` reste inchangé.

Les données sont statiques et locales. Les exercices sont textuels, les tirages
peuvent se répéter et les niveaux ne sont pas étalonnés pédagogiquement.
Ce module n'est pas relié aux pages interactives du site.
