# Catalogue JSON des exercices

Ce dossier est la source des données statiques du générateur Python et du
backend. Un fichier UTF-8 par famille : `association.json`, `intrus.json`,
`denombrement.json`. Les énoncés, contenus et paramètres des niveaux sont
éditables ici, sans modifier le Python.

## Structure commune

Chaque document contient :

- `version` : version du format, actuellement l'entier `1`.
- `type` : nom de la famille, identique au nom du fichier sans extension.
- `enonce` : consigne ou modèle de consigne.
- `difficultes` : objets correspondant aux clés `"1"`, `"2"`, `"3"`.
- `modeles` : liste non vide de contenus dans lesquels effectuer les tirages.

## Particularités des familles

| Fichier | Contenu d'un modèle | Paramètres d'un niveau |
| --- | --- | --- |
| `association.json` | `paires` : listes `[mot, correspondant]` | `nombre_paires` |
| `intrus.json` | `elements` de même famille et `intrus` distinct | `nombre_elements`, sans compter l'intrus |
| `denombrement.json` | `element` au singulier et `pluriel` explicite | `minimum` et `maximum`, bornes incluses |

Pour une association, chaque modèle doit avoir suffisamment de paires pour
tous les niveaux ; les mots de gauche et ceux de droite doivent être uniques
dans ce modèle. Pour l'intrus, prévoir suffisamment d'éléments distincts et
ne pas inclure l'intrus parmi eux. Les nombres d'éléments et de paires doivent
être des entiers positifs. Pour le dénombrement, utiliser des bornes entières
positives avec `minimum <= maximum` ; la consigne utilise `{nom}` et
`{elements}`, remplacés au tirage.

Les réglages actuels conservent trois, quatre et cinq paires ou éléments de
famille selon le niveau, et des quantités de 1–5, 4–10 et 8–20 à compter.
Le chargeur vérifie la structure commune ; les contraintes propres aux
modèles doivent être respectées lors de l'édition.

Les chemins sont calculés depuis le module, indépendamment du répertoire de
lancement. Chaque fichier est chargé à sa première utilisation et mis en
cache pour le processus : redémarrer le serveur après une modification.
Un fichier absent, un JSON illisible ou une structure commune invalide
provoque une erreur explicite ; aucun catalogue Python de secours n'est utilisé.

Ce sont les modèles sources, pas un répertoire d'export des exercices tirés.
Les séances générées restent enregistrées en JSON dans SQLite ; la modification
d'un modèle ne change pas les séances existantes. Les fichiers `data.js` de
l'interface autonome ne sont pas consommés par ce générateur et restent inchangés.
