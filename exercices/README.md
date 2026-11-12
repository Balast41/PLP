# Exercices interactifs

Trois exercices indépendants. Ouvre le `index.html` de chaque dossier dans un navigateur (aucun serveur ni installation nécessaire).

| Dossier        | Exercice                                  |
|----------------|-------------------------------------------|
| `association/` | Relier une image à son mot                |
| `memory/`      | Jeu de memory (carte image + carte mot)   |
| `intrus/`      | Trouver le mot qui n'a pas de lien        |

## Structure de chaque dossier

- `index.html` : la page (structure)
- `style.css`  : l'apparence
- `script.js`  : la logique du jeu
- `data.js`    : le contenu de l'exercice (**c'est le seul fichier à modifier pour changer les questions**)

## Enchaîner les exercices

Il n'y a plus de score, de bouton ni de message de fin : quand l'élève a terminé, l'exercice passe tout seul à la suite.
Dans `data.js`, la constante `SUIVANT` indique où aller (ex. `"../memory/index.html"`).
Avec `null`, l'exercice recommence avec un nouveau mélange.

## Changer le contenu

Édite `data.js`. Pour l'association et le memory, le champ `image` accepte un emoji
(`"🐱"`) ou un chemin vers une image placée dans le dossier `img/` (`"img/chat.png"`).

Pourquoi `data.js` et pas un `.json` ? Un navigateur refuse de charger un fichier JSON
avec `fetch` quand la page est ouverte par double-clic (`file://`). Un fichier `.js` fonctionne partout.
Si tu héberges le site sur un serveur, tu pourras passer à du JSON + `fetch` sans toucher au reste.
