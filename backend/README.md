# Backend PLP

API FastAPI pour le générateur Python existant : association, intrus et
dénombrement. Python 3.10 minimum. Toutes les commandes partent de la racine
du dépôt `PLP-github`.

## Installation et démarrage

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --reload
```

Sur Linux/macOS, remplacer `backend/.venv/Scripts/python` par
`backend/.venv/bin/python`. Le serveur écoute sur `http://127.0.0.1:8000`.

## Documentation des endpoints

Les schémas détaillés et les essais interactifs se trouvent dans
`http://127.0.0.1:8000/docs` (Swagger), `/redoc` (lecture) et
`/openapi.json` (contrat machine). Ces trois routes techniques répondent en
200 sans paramètre ; elles ne créent aucun exercice.

### GET /health

Vérifie que le processus répond. Aucun paramètre ni corps.
Réponse 200 : `{"status":"ok"}`.

### GET /api/v1/exercise-types

Liste les types et niveaux disponibles. Aucun paramètre ni corps.
Réponse 200 :

```json
{"types":["association","intrus","denombrement"],"difficultes":[1,2,3]}
```

### POST /api/v1/exercises

Génère un exercice et le conserve temporairement côté serveur.
Corps JSON requis ; `{}` utilise les valeurs par défaut :

| Champ | Type | Défaut | Valeurs |
| --- | --- | --- | --- |
| type | chaîne ou null | null | association, intrus, denombrement ; null choisit au hasard |
| difficulty | entier | 1 | 1, 2 ou 3 ; booléens et chaînes refusés |

Les champs supplémentaires sont refusés. Réponse 201 avec un en-tête
`Location: /api/v1/exercises/<identifiant>` et un corps de cette forme
(exemple illustratif, le tirage varie) :

```json
{
  "identifiant": "0123456789abcdef0123456789abcdef",
  "type": "denombrement",
  "difficulte": 1,
  "enonce": "Compte les pommes : pomme | pomme | pomme",
  "propositions": [2, 3, 4, 5]
}
```

`propositions` contient une liste de nombres pour le dénombrement, une liste
de mots pour l'intrus, ou un objet `{"elements":[...],"correspondances":[...]}`
pour l'association. `bonne_reponse` reste côté serveur ; la fonction Python
originale conserve son contrat et retourne toujours la solution.
Erreur 422 : type, niveau ou corps invalide.

Exemple PowerShell :

```powershell
$exercice = Invoke-RestMethod http://127.0.0.1:8000/api/v1/exercises -Method Post -ContentType 'application/json' -Body '{"type":"denombrement","difficulty":1}'
$exercice
```

### GET /api/v1/exercises/{identifier}

Récupère un exercice déjà généré, sans la solution. `identifier` est un UUID
(32 caractères hexadécimaux, ou forme avec tirets). Aucun corps.
Réponse 200 : même structure que la génération.
Erreur 404 : identifiant inconnu, cache évincé ou serveur redémarré.
Erreur 422 : identifiant mal formé.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/exercises/$($exercice.identifiant)"
```

### POST /api/v1/exercises/{identifier}/answers

Corrige une réponse. Même format d'identifiant que la récupération.
Corps JSON avec le seul champ obligatoire `reponse` :

| Type d'exercice | Exemple de corps |
| --- | --- |
| intrus | `{"reponse":"chaise"}` |
| denombrement | `{"reponse":3}` |
| association | `{"reponse":{"chat":"animal","pomme":"fruit","chaise":"meuble"}}` |

La comparaison est exacte : casse et accents comptent ; pour l'association,
toutes les paires doivent être présentes et l'ordre des clés ne compte pas.
Une réponse du bon format mais incorrecte renvoie 200 avec `correcte: false`.
Réponse 200 pour une réponse correcte à l'exemple de dénombrement :

```json
{"identifiant":"0123456789abcdef0123456789abcdef","correcte":true,"bonne_reponse":3}
```

Erreur 404 : exercice absent du cache. Erreur 422 : UUID, corps ou format
invalide (par exemple une chaîne pour le dénombrement). Une correction révèle
la solution et peut être redemandée ; aucun résultat n'est stocké.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/exercises/$($exercice.identifiant)/answers" -Method Post -ContentType 'application/json' -Body '{"reponse":3}'
```

### Format des erreurs

Les erreurs 404 et les incompatibilités de format de réponse sont des objets
`{"detail":"message"}`. Les validations FastAPI/Pydantic renvoient en 422
`{"detail":[...]}` avec les champs `loc`, `msg` et `type` décrivant l'erreur.

## Tests

```powershell
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python -m unittest backend.test_api -v
```

Les tests couvrent les trois types aux trois niveaux, la correction, les
erreurs, le cache, CORS et le contrat OpenAPI.

## Configuration et limites

Les origines CORS autorisées par défaut sont `http://localhost:5500` et
`http://127.0.0.1:5500`. Configurer d'autres origines avant le démarrage :

```powershell
$env:PLP_CORS_ORIGINS = 'http://localhost:3000,https://exemple.fr'
```

Utiliser une origine HTTP pour les pages clientes. Le frontend existant reste
autonome ; son raccordement à l'API est à effectuer séparément.

Le cache conserve les 1 000 derniers exercices, évince le plus ancien et se
vide au redémarrage. Utiliser un seul worker : les caches ne sont pas partagés
entre processus. Aucun compte, authentification, donnée personnelle, historique,
base de données ni service externe. Les pages login/register existantes n'ont
pas de backend dans ce périmètre pédagogique. Les exercices memory ne font
pas partie des trois types du générateur actuel. Niveaux et vocabulaire restent
ceux du MVP ; aucune garantie d'unicité des contenus tirés.

Références : [modèles de réponse FastAPI](https://fastapi.tiangolo.com/tutorial/response-model/)
et [tests HTTP FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).
