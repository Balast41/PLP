# Exemples de requêtes pour l'API ApprenTSAge

Ce guide couvre chaque endpoint applicatif et les routes de documentation.
Les blocs `http` sont des modèles à utiliser dans un client HTTP, Postman,
ou à reproduire dans Swagger (`http://127.0.0.1:8000/docs`). Ce ne sont pas
des commandes à coller directement dans PowerShell.

## Préparer les exemples

Depuis la racine du dépôt, démarrer le serveur :

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Remplacer les variables entre doubles accolades par les valeurs réelles.
Pour une saisie manuelle, remplacer aussi les accolades :
`{{baseUrl}}/health` devient `http://127.0.0.1:8000/health`.

| Variable | Valeur ou provenance |
| --- | --- |
| `baseUrl` | `http://127.0.0.1:8000`, sans barre oblique finale |
| `teacherToken` | `access_token` de la connexion de l'enseignant responsable |
| `parentToken` | Jeton du compte `parent.demo@example.test` |
| `adminToken` | Jeton obtenu après connexion d'un administrateur créé localement |
| `learnerId` | `id` renvoyé à la création du profil élève |
| `invitationToken` | `token` renvoyé par la création d'invitation |
| `memberUserId` | `id` du parent dans la liste des membres du profil |
| `sessionId` | `id` d'une séance ouverte, pour réponses puis clôture |
| `sessionToCancelId` | `id` d'une autre séance ouverte à abandonner |
| `associationExerciseId` | `identifiant` d'un exercice d'association de `sessionId` |
| `intrusExerciseId` | `identifiant` d'un exercice intrus de `sessionId` |
| `countingExerciseId` | `identifiant` d'un dénombrement de `sessionId` |
| `demoExerciseId` | `identifiant` renvoyé par la génération indépendante de démonstration |
| `targetUserId` | `id` d'un compte adulte non administrateur à gérer |

Les identifiants de démonstration et les identifiants de séances persistantes
ne sont pas interchangeables. `id` désigne les profils/comptes/séances ;
`identifiant` désigne un exercice.

Les données d'exemple sont fictives. Les mots de passe ci-dessous servent
uniquement aux essais locaux et ne sont pas des secrets de déploiement.
Ne pas envoyer de champ supplémentaire comme `confirmPassword` : il serait
refusé. La casse et les accents des réponses comptent.

Parcours conseillé : inscrire et connecter l'enseignant, créer un profil,
inviter le parent, créer une évaluation initiale, répondre à tous ses exercices,
la clôturer avec un adulte, puis lire progression et recommandations.
Les sections ne forment pas un script à exécuter intégralement dans l'ordre :
déconnexion, changement de mot de passe, suspension, retrait d'accès et
suppression sont des exemples indépendants à tester en dernier.

## Comptes

### POST /api/v1/auth/register

Créer un enseignant. Réponse attendue : 201 et un compte public, sans mot de passe.

```http
POST {{baseUrl}}/api/v1/auth/register
Content-Type: application/json

{"username":"Enseignant démo","email":"teacher.demo@example.test","password":"Demo-local-enseignant-2026!","role":"teacher"}
```

Pour tester les invitations, créer aussi le parent :

```http
POST {{baseUrl}}/api/v1/auth/register
Content-Type: application/json

{"username":"Parent démo","email":"parent.demo@example.test","password":"Demo-local-parent-2026!","role":"parent"}
```

Autres rôles publics : `support` et `child`. `admin` est refusé (422).
Un email déjà inscrit provoque 409 ; utiliser ensuite la connexion.

### POST /api/v1/auth/login

Réponse attendue : 200 avec `access_token`. Copier ce jeton dans `teacherToken`.

```http
POST {{baseUrl}}/api/v1/auth/login
Content-Type: application/json

{"email":"teacher.demo@example.test","password":"Demo-local-enseignant-2026!"}
```

Se connecter séparément comme parent pour remplir `parentToken` :

```http
POST {{baseUrl}}/api/v1/auth/login
Content-Type: application/json

{"email":"parent.demo@example.test","password":"Demo-local-parent-2026!"}
```

Le jeton expire après douze heures. 401 : identifiants incorrects ou compte
suspendu ; 429 : blocage temporaire après cinq échecs.

### GET /api/v1/users/me

Consulter le compte courant. Réponse attendue : 200.

```http
GET {{baseUrl}}/api/v1/users/me
Authorization: Bearer {{teacherToken}}
```

### PATCH /api/v1/users/me

Modifier le nom affiché, sans modifier le rôle ou l'email. Réponse : 200.

```http
PATCH {{baseUrl}}/api/v1/users/me
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"username":"Enseignant de démonstration"}
```

### PUT /api/v1/users/me/password

Changer le mot de passe. Réponse : 204 sans corps. Cette opération révoque
tous les jetons de ce compte, y compris `teacherToken` : se reconnecter avec
le nouveau mot de passe avant d'effectuer d'autres requêtes.

```http
PUT {{baseUrl}}/api/v1/users/me/password
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"current_password":"Demo-local-enseignant-2026!","new_password":"Nouveau-demo-local-2026!"}
```

### POST /api/v1/auth/logout

Révoquer seulement le jeton présenté. Réponse : 204 sans corps.

```http
POST {{baseUrl}}/api/v1/auth/logout
Authorization: Bearer {{teacherToken}}
```

## Profils élèves

### POST /api/v1/learners

L'enseignant devient responsable du profil. Copier `id` dans `learnerId`.
Réponse : 201. L'administrateur, le parent ou l'accompagnant peuvent aussi
créer un profil ; un compte élève ne le peut pas (403).

```http
POST {{baseUrl}}/api/v1/learners
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"name":"Élève démo","audio":false}
```

### GET /api/v1/learners

Lister les profils accessibles. Réponse : 200, tableau paginé.

```http
GET {{baseUrl}}/api/v1/learners?limit=20&offset=0
Authorization: Bearer {{teacherToken}}
```

### GET /api/v1/learners/{learner_id}

Lire le profil. Réponse : 200 ; 404 si le compte n'y a pas accès.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}
Authorization: Bearer {{teacherToken}}
```

### PATCH /api/v1/learners/{learner_id}

Modifier le nom et la préférence audio avec un adulte lié. Envoyer les deux
valeurs souhaitées : l'omission d'`audio` remet sa valeur par défaut à false.
Réponse : 200. Le backend n'effectue pas de lecture audio.

```http
PATCH {{baseUrl}}/api/v1/learners/{{learnerId}}
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"name":"Profil élève démo","audio":true}
```

### DELETE /api/v1/learners/{learner_id}

Exemple à tester en dernier sur un profil de démonstration. Réservé au
responsable ou à l'administrateur. Supprime définitivement le profil,
ses séances et résultats, son programme, ses invitations et ses accès.
Réponse : 204 sans corps.

```http
DELETE {{baseUrl}}/api/v1/learners/{{learnerId}}
Authorization: Bearer {{teacherToken}}
```

## Invitations et accès

### POST /api/v1/learners/{learner_id}/invitations

Inviter le parent avec le compte responsable. Copier `token` dans
`invitationToken` et le transmettre au destinataire. Réponse : 201.

```http
POST {{baseUrl}}/api/v1/learners/{{learnerId}}/invitations
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"email":"parent.demo@example.test"}
```

### POST /api/v1/invitations/accept

Utiliser le jeton de connexion du destinataire, pas celui de l'enseignant.
Le parent doit être inscrit et connecté avec l'email invité. Réponse : 200
avec `learner_id`. 404 si l'invitation est expirée, utilisée ou vise un autre compte.

```http
POST {{baseUrl}}/api/v1/invitations/accept
Authorization: Bearer {{parentToken}}
Content-Type: application/json

{"token":"{{invitationToken}}"}
```

La même procédure permet d'inviter un accompagnant, un autre enseignant ou
le compte élève. Un compte élève déjà lié à un profil reçoit 409.

### GET /api/v1/learners/{learner_id}/members

Lister les comptes liés avec un adulte autorisé. Copier l'`id` du parent
dans `memberUserId`. Réponse : 200.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}/members
Authorization: Bearer {{teacherToken}}
```

### DELETE /api/v1/learners/{learner_id}/members/{user_id}

Retirer l'accès du parent avec le responsable. Réponse : 204. Le compte parent
continue d'exister, mais perd immédiatement l'accès à ce profil. Le retrait
du responsable lui-même est refusé (409).

```http
DELETE {{baseUrl}}/api/v1/learners/{{learnerId}}/members/{{memberUserId}}
Authorization: Bearer {{teacherToken}}
```

## Compétences, progression et recommandations

### GET /api/v1/skills

Réponse : 200, liste des compétences et types associés.

```http
GET {{baseUrl}}/api/v1/skills
Authorization: Bearer {{teacherToken}}
```

### GET /api/v1/learners/{learner_id}/curriculum

Lire les objectifs pédagogiques du profil. Réponse : 200, objet `skills`.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}/curriculum
Authorization: Bearer {{teacherToken}}
```

### PUT /api/v1/learners/{learner_id}/curriculum

Remplacer la liste des objectifs avec un enseignant lié ou un administrateur.
Un parent ou accompagnant reçoit 403. Il faut une liste non vide, sans doublon.
Réponse : 200. Garder les trois valeurs permet de tester toutes les familles.

```http
PUT {{baseUrl}}/api/v1/learners/{{learnerId}}/curriculum
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"skills":["vocabulaire","categorisation","numeration"]}
```

### GET /api/v1/learners/{learner_id}/progress

Lire les états de maîtrise et les règles floues activées. Réponse : 200.
Avant une séance éligible terminée, les compétences sont non évaluées.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}/progress
Authorization: Bearer {{teacherToken}}
```

### GET /api/v1/learners/{learner_id}/recommendations

Lire `initial_assessment_required` et la liste `activities` ordonnée par
priorité, avec type et difficulté proposés. Réponse : 200.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}/recommendations
Authorization: Bearer {{teacherToken}}
```

## Séances persistantes

### POST /api/v1/learners/{learner_id}/sessions

Commencer par une évaluation initiale de trois exercices, un par compétence.
Copier `id` dans `sessionId` et les `identifiant` des trois exercices dans
les variables correspondant à leur `type`. Réponse : 201, séance et exercices
sans les solutions.

```http
POST {{baseUrl}}/api/v1/learners/{{learnerId}}/sessions
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"mode":"initial","difficulty":2,"count":3}
```

Après clôture de l'évaluation initiale, demander une séance évaluée adaptée
automatiquement (type et difficulté sont déduits) :

```http
POST {{baseUrl}}/api/v1/learners/{{learnerId}}/sessions
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"mode":"evaluated","count":5}
```

Créer un entraînement libre de dénombrement, sans effet sur le suivi.
Un parent invité peut faire cette requête si `numeration` est dans le programme :

```http
POST {{baseUrl}}/api/v1/learners/{{learnerId}}/sessions
Authorization: Bearer {{parentToken}}
Content-Type: application/json

{"mode":"practice","type":"denombrement","difficulty":1,"count":3}
```

Le nombre doit être compris entre 3 et 20. Un mode évalué avant l'évaluation
initiale terminée provoque 409. Un type hors programme provoque 403.
En mode initial, ne pas préciser `type` : l'évaluation couvre les trois types.

### GET /api/v1/learners/{learner_id}/sessions

Historique des séances, des plus récentes aux plus anciennes. Réponse : 200.

```http
GET {{baseUrl}}/api/v1/learners/{{learnerId}}/sessions?limit=20&offset=0
Authorization: Bearer {{teacherToken}}
```

### GET /api/v1/sessions/{session_id}

Reprendre une séance : le résultat contient les exercices et leur indicateur
`answered`. Réponse : 200. Le tirage ne change pas lors de cette lecture.

```http
GET {{baseUrl}}/api/v1/sessions/{{sessionId}}
Authorization: Bearer {{teacherToken}}
```

### POST /api/v1/sessions/{session_id}/exercises/{exercise_id}/answers

Utiliser l'identifiant d'un exercice de la séance, avec une réponse du bon
format. Les valeurs ci-dessous sont illustratives : les adapter au tirage.
Une réponse du bon format peut être fausse ; elle renvoie alors 200 et
`correcte:false` avec la solution. Il n'est pas garanti que ces exemples
soient corrects pour votre exercice.

Association : envoyer toutes les paires proposées pour espérer une réponse correcte.

```http
POST {{baseUrl}}/api/v1/sessions/{{sessionId}}/exercises/{{associationExerciseId}}/answers
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"reponse":{"chat":"animal","pomme":"fruit","chaise":"meuble"},"elapsed_seconds":18.5}
```

Intrus : une chaîne de caractères.

```http
POST {{baseUrl}}/api/v1/sessions/{{sessionId}}/exercises/{{intrusExerciseId}}/answers
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"reponse":"chaise","elapsed_seconds":8}
```

Dénombrement : un entier, ni une chaîne `"3"`, ni un booléen.

```http
POST {{baseUrl}}/api/v1/sessions/{{sessionId}}/exercises/{{countingExerciseId}}/answers
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"reponse":3,"elapsed_seconds":12}
```

Une seule soumission par exercice : un deuxième essai renvoie 409 et ne
remplace pas la première réponse. Le temps est facultatif, de 0 à 86400 secondes.

### POST /api/v1/sessions/{session_id}/complete

Après toutes les réponses, un adulte lié déclare l'accompagnement et clôture
la séance. Réponse : 200. Un compte élève reçoit 403 ; des réponses manquantes
ou une séance déjà fermée provoquent 409.

```http
POST {{baseUrl}}/api/v1/sessions/{{sessionId}}/complete
Authorization: Bearer {{teacherToken}}
Content-Type: application/json

{"assistance":"partiel","notes":"Consigne reformulée au début, puis réalisation avec une aide ponctuelle."}
```

Autres valeurs : `total`, `allege`, `autonome`. Les notes sont facultatives,
limitées à 2 000 caractères. Une séance `practice` clôturée reste exclue du suivi.

### POST /api/v1/sessions/{session_id}/cancel

Utiliser une autre séance encore ouverte, dont l'identifiant est dans
`sessionToCancelId`. Réponse : 200 avec `status:"cancelled"`. Elle ne comptera
pas dans le suivi. Une séance déjà fermée reçoit 409.

```http
POST {{baseUrl}}/api/v1/sessions/{{sessionToCancelId}}/cancel
Authorization: Bearer {{teacherToken}}
```

## Administration

Créer d'abord un compte administrateur sur le serveur :

```powershell
python -m backend.manage create-admin
```

Se connecter ensuite par `POST /api/v1/auth/login` avec les identifiants saisis
et copier le jeton obtenu dans `adminToken`. Un jeton d'enseignant ne donne
pas accès aux routes d'administration : il renverrait 403.

### GET /api/v1/admin/users

Lister les comptes. Copier l'identifiant d'un compte adulte de démonstration
non administrateur dans `targetUserId`. Réponse : 200.

```http
GET {{baseUrl}}/api/v1/admin/users?limit=20&offset=0
Authorization: Bearer {{adminToken}}
```

### PATCH /api/v1/admin/users/{user_id}/status

Suspendre le compte cible et révoquer ses connexions. Réponse : 200.
Ne pas suspendre un compte nécessaire à la suite de votre démonstration.

```http
PATCH {{baseUrl}}/api/v1/admin/users/{{targetUserId}}/status
Authorization: Bearer {{adminToken}}
Content-Type: application/json

{"active":false}
```

Pour réactiver le compte, envoyer la même requête avec `{"active":true}`.
Le compte devra se reconnecter. Cibler un administrateur est refusé (403).

### PATCH /api/v1/admin/users/{user_id}/role

Changer un rôle adulte, par exemple passer un parent de démonstration au rôle
d'accompagnant. Réponse : 200, avec révocation des connexions du compte cible.

```http
PATCH {{baseUrl}}/api/v1/admin/users/{{targetUserId}}/role
Authorization: Bearer {{adminToken}}
Content-Type: application/json

{"role":"support"}
```

Autres valeurs adultes : `parent`, `teacher`. Les conversions vers ou depuis
un élève, ainsi que les modifications d'administrateur, sont interdites.

### GET /api/v1/admin/stats

Obtenir les nombres de comptes, profils, séances et exercices de séances.
Réponse : 200. Les exercices indépendants de démonstration ne sont pas comptés.

```http
GET {{baseUrl}}/api/v1/admin/stats
Authorization: Bearer {{adminToken}}
```

## Exercices indépendants de démonstration

Ces routes sont publiques, sans compte ni suivi d'élève. Elles utilisent un
cache temporaire distinct de la base des séances. Le cache est perdu au
redémarrage et ne conserve que les 1 000 derniers exercices.

### GET /api/v1/exercise-types

Lister les types et difficultés possibles. Réponse : 200.

```http
GET {{baseUrl}}/api/v1/exercise-types
```

### POST /api/v1/exercises

Générer un dénombrement. Copier `identifiant` dans `demoExerciseId`.
Réponse : 201, avec en-tête `Location` et exercice sans solution.

```http
POST {{baseUrl}}/api/v1/exercises
Content-Type: application/json

{"type":"denombrement","difficulty":1}
```

Pour une association ou un intrus, remplacer `type` par `association` ou `intrus`.
Pour un type aléatoire au niveau 1, envoyer `{}`. La difficulté doit être un
entier entre 1 et 3. Le corps JSON reste requis.

### GET /api/v1/exercises/{identifier}

Relire l'exercice de démonstration généré. Réponse : 200 ; 404 si absent ou
évincé du cache ; 422 si l'identifiant n'est pas un UUID valide.

```http
GET {{baseUrl}}/api/v1/exercises/{{demoExerciseId}}
```

### POST /api/v1/exercises/{identifier}/answers

Corriger une proposition pour le dénombrement généré ci-dessus. Adapter la
valeur au comptage réel. Réponse : 200 avec `correcte` et `bonne_reponse`.
Aucun résultat n'est enregistré dans le suivi.

```http
POST {{baseUrl}}/api/v1/exercises/{{demoExerciseId}}/answers
Content-Type: application/json

{"reponse":3}
```

Pour un intrus : `{"reponse":"chaise"}`. Pour une association :
`{"reponse":{"chat":"animal","pomme":"fruit","chaise":"meuble"}}`.
Ces corps sont des exemples de forme, à adapter aux propositions réellement
reçues. Contrairement aux séances persistantes, cette route de démonstration
n'empêche pas les corrections répétées.

## Service et documentation technique

### GET /health

Vérifier que le processus répond. Cette route ne vérifie pas l'état de SQLite.
Réponse : 200, `{"status":"ok"}`.

```http
GET {{baseUrl}}/health
```

### GET /docs

Afficher Swagger dans un navigateur. Réponse : 200, page HTML.

```http
GET {{baseUrl}}/docs
```

### GET /redoc

Afficher la documentation de lecture. Réponse : 200, page HTML.

```http
GET {{baseUrl}}/redoc
```

### GET /openapi.json

Lire le contrat de l'API : routes, modèles, validations et sécurité.
Réponse : 200, document JSON.

```http
GET {{baseUrl}}/openapi.json
```

### GET /docs/oauth2-redirect

Page technique installée automatiquement par FastAPI pour Swagger. Elle
n'est pas un endpoint de connexion métier et ne remplace pas `/auth/login`.
L'application actuelle utilise des jetons Bearer opaques, sans flux OAuth2
configuré. Réponse : 200, page HTML.

```http
GET {{baseUrl}}/docs/oauth2-redirect
```

## Lire les erreurs et retrouver la documentation

| Code | Signification générale |
| --- | --- |
| 200 | Action effectuée avec un corps de réponse |
| 201 | Ressource créée |
| 204 | Action effectuée, sans corps de réponse |
| 401 | Connexion requise, jeton invalide/expiré ou compte suspendu |
| 403 | Le rôle ou le programme pédagogique interdit l'action |
| 404 | Ressource absente ou inaccessible au compte courant |
| 409 | Conflit : doublon, réponse déjà enregistrée, séance fermée ou prérequis absent |
| 422 | Données invalides ou format de réponse incompatible |
| 429 | Trop d'échecs de connexion pour cette adresse |

Les listes acceptent `limit` entre 1 et 100 et un `offset` positif ou nul.
Les erreurs métier contiennent `{"detail":"message"}` ; les validations
FastAPI/Pydantic contiennent généralement `{"detail":[...]}`.
Toutes les variables doivent être remplacées avant l'envoi.

Pour les règles détaillées : [plateforme](backend/PLATEFORME.md),
[logique floue](backend/LOGIQUE_FLOUE.md) et [explication globale](Explications.md).
