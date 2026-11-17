# API de la plateforme ApprenTSAge

## Démarrer

Depuis la racine du dépôt, installer `backend/requirements.txt`, puis lancer :

```powershell
python -m uvicorn backend.main:app --reload
```

Documentation interactive de toutes les routes et de tous leurs schémas :
`http://127.0.0.1:8000/docs`. Contrat OpenAPI : `/openapi.json`.
Toutes les routes de ce document commencent par `/api/v1`.
Le frontend n'est pas modifié : ses formulaires de démonstration doivent être
raccordés à ces endpoints pour utiliser la véritable authentification.

## Comptes et authentification

Inscription et connexion sont publiques ; toutes les autres routes de ce
document exigent `Authorization: Bearer <access_token>`. Dans Swagger,
copier le jeton issu de la connexion dans le bouton **Authorize**.

| Méthode et chemin | Entrée | Succès et sortie | Erreurs spécifiques |
| --- | --- | --- | --- |
| POST `/auth/register` | `{username,email,password,role}` | 201, compte public | 409 email déjà utilisé ; 422 champs invalides |
| POST `/auth/login` | `{email,password}` | 200, `{access_token,token_type:"bearer",expires_in:43200,user}` | 401 identifiants invalides/compte suspendu ; 429 après 5 échecs |
| POST `/auth/logout` | Aucun corps | 204, jeton courant révoqué | 401 jeton absent/expiré |
| GET `/users/me` | Aucun corps | 200, compte public | 401 |
| PATCH `/users/me` | `{username}` | 200, compte mis à jour | 422 nom invalide |
| PUT `/users/me/password` | `{current_password,new_password}` | 204, toutes les sessions révoquées | 403 ancien mot de passe incorrect ; 422 nouveau mot de passe invalide |

Un compte public contient `id`, `username`, `email`, `role`, `active`,
`created_at`. Jamais de hash de mot de passe ni de jeton stocké.
Rôles d'inscription : `child` (élève, quel que soit son âge), `teacher`,
`parent`, `support`. `admin` est créé uniquement par commande locale.
Nom : 1 à 100 caractères ; mot de passe : 12 à 128 caractères. Les emails
sont normalisés en minuscules et contrôlés syntaxiquement, sans vérification
de boîte mail. Aucun champ `confirmPassword` côté serveur : cette confirmation
reste dans l'interface. Les champs inconnus sont refusés.

Les mots de passe utilisent scrypt avec sel aléatoire ; les jetons opaques
sont stockés sous forme de digest SHA-256 et expirent après 12 heures.
Une modification de mot de passe, une suspension ou un changement de rôle
révoque les sessions du compte concerné. Le blocage après cinq échecs est
local à l'email et dure 15 minutes ; une connexion réussie remet le compteur
à zéro. Le jeton n'est renvoyé qu'à la connexion. Pas de refresh token :
se reconnecter après expiration.

### Exemple PowerShell

```powershell
$base = 'http://127.0.0.1:8000/api/v1'
Invoke-RestMethod "$base/auth/register" -Method Post -ContentType 'application/json' -Body '{"username":"Prof démo","email":"prof@example.test","password":"Exemple-mot-de-passe-123","role":"teacher"}'
$login = Invoke-RestMethod "$base/auth/login" -Method Post -ContentType 'application/json' -Body '{"email":"prof@example.test","password":"Exemple-mot-de-passe-123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$eleve = Invoke-RestMethod "$base/learners" -Headers $headers -Method Post -ContentType 'application/json' -Body '{"name":"Élève démo","audio":false}'
```

## Profils élèves et permissions

Un profil élève est distinct d'un compte de connexion. Un adulte crée le
profil et en devient responsable (`owner_id`). Il peut partager l'accès par
invitation nominative. Un compte `child` ne peut accepter qu'un lien élève.
Les trois compétences sont initialement actives pour chaque nouveau profil.

| Méthode et chemin | Entrée | Succès et sortie | Permission / erreurs spécifiques |
| --- | --- | --- | --- |
| POST `/learners` | `{name,audio:false}` | 201, profil | Adulte ; 403 élève ; 422 nom invalide |
| GET `/learners` | `limit=50`, `offset=0` | 200, liste de profils accessibles | Tous les profils pour admin |
| GET `/learners/{learner_id}` | Identifiant du profil | 200, profil | Compte lié ou admin ; sinon 404 |
| PATCH `/learners/{learner_id}` | `{name,audio:false}` | 200, profil mis à jour | Adulte lié ou admin ; sinon 403/404 |
| DELETE `/learners/{learner_id}` | Aucun corps | 204 | Responsable ou admin ; sinon 403/404 |
| POST `/learners/{learner_id}/invitations` | `{email}` | 201, `{token,expires_at}` | Responsable ou admin ; sinon 403/404 |
| POST `/invitations/accept` | `{token}` | 200, `{learner_id}` | Email du compte connecté identique à l'invitation ; 404 jeton invalide/expiré ; 409 élève déjà lié |
| GET `/learners/{learner_id}/members` | Aucun corps | 200, liste de comptes publics | Adulte lié ou admin ; sinon 403/404 |
| DELETE `/learners/{learner_id}/members/{user_id}` | Aucun corps | 204 | Responsable ou admin ; 409 retrait du responsable ; absence de membre : 204 |

Profil : `{id,name,owner_id,audio,created_at}`. Les listes sont paginées :
`limit` de 1 à 100, `offset` entier positif ou nul. L'invitation expire en
48 heures, est utilisable une seule fois et doit être transmise par le
responsable (aucun email automatique). Le retrait d'accès bloque immédiatement
la lecture des séances et résultats associés. Supprimer un profil efface
ses liens, invitations, compétences, séances et résultats par cascade.

L'administrateur a accès à tous les profils. Les autres utilisateurs doivent
être explicitement liés : connaître un identifiant ne donne aucun droit.
Les rôles déclarés à l'inscription ne donnent pas accès aux profils existants.
Le prototype ne vérifie pas la qualification professionnelle d'un enseignant
ni l'identité du détenteur d'une adresse email.

## Compétences et recommandations

| Méthode et chemin | Entrée | Succès et sortie | Permission / erreurs spécifiques |
| --- | --- | --- | --- |
| GET `/skills` | Aucun corps | 200, `[{id,exercise_type}]` | Tout compte authentifié |
| GET `/learners/{learner_id}/curriculum` | Aucun corps | 200, `{skills:[...]}` | Compte lié ou admin ; sinon 404 |
| PUT `/learners/{learner_id}/curriculum` | `{skills:[...]}` | 200, compétences sélectionnées | Enseignant lié ou admin ; 403 parent/accompagnant/élève ; 422 liste vide, doublons ou valeur inconnue |
| GET `/learners/{learner_id}/progress` | Aucun corps | 200, objet indexé par compétence | Compte lié ou admin ; sinon 404 |
| GET `/learners/{learner_id}/recommendations` | Aucun corps | 200, `{initial_assessment_required,activities:[...]}` | Compte lié ou admin ; sinon 404 |

Compétences prises en charge : `vocabulaire` → `association`,
`categorisation` → `intrus`, `numeration` → `denombrement`. Les parents et
accompagnants peuvent choisir un type d'exercice parmi les compétences
prévues, mais ne peuvent pas modifier ces objectifs. Le changement du plan
n'altère pas les séances déjà créées : leur contenu reste figé.

Chaque progression contient : `etat`, `score` (0 à 1 ou null), `seances`
(nombre de séances clôturées comptabilisées), `confirmations`, `difficulty`
(1 à 3) et `inference`. L'inférence détaille les degrés d'appartenance et les
règles activées. Les recommandations ajoutent `skill` et `type`, sont filtrées
par les compétences actives et classées par maîtrise croissante. Les activités
non évaluées passent en premier. Voir [LOGIQUE_FLOUE.md](LOGIQUE_FLOUE.md).

## Séances et réponses

| Méthode et chemin | Entrée | Succès et sortie | Erreurs spécifiques |
| --- | --- | --- | --- |
| POST `/learners/{learner_id}/sessions` | `{mode:"evaluated",type:null,difficulty:null,count:5}` | 201, séance détaillée | 403 compétence hors plan ; 409 évaluation initiale manquante ; 422 options invalides |
| GET `/learners/{learner_id}/sessions` | `limit=50`, `offset=0` | 200, résumés du plus récent au plus ancien | 404 profil inaccessible |
| GET `/sessions/{session_id}` | Aucun corps | 200, séance détaillée | 404 séance inconnue/inaccessible |
| POST `/sessions/{session_id}/exercises/{exercise_id}/answers` | `{reponse,elapsed_seconds:0}` | 200, `{identifiant,correcte,bonne_reponse}` | 404 exercice absent ; 409 réponse déjà enregistrée ou séance fermée ; 422 format incompatible |
| POST `/sessions/{session_id}/complete` | `{assistance,notes:""}` | 200, résumé clôturé | 403 compte élève ; 409 réponses manquantes ou séance fermée |
| POST `/sessions/{session_id}/cancel` | Aucun corps | 200, `{id,status:"cancelled"}` | 409 séance déjà fermée |

Toutes ces routes exigent un compte lié au profil ou un administrateur.
Seule la clôture avec accompagnement est réservée à un adulte.

Modes :

- `initial` répartit les exercices sur les trois compétences, au niveau 2
  par défaut. `type` doit être omis ou null. L'évaluation initiale couvre
  l'ensemble du catalogue même si le plan courant est plus restreint.
- `evaluated` exige une évaluation initiale clôturée. Sans type, la compétence
  active la moins maîtrisée est choisie ; sans difficulté, le moteur la déduit.
- `practice` permet l'entraînement dès le début et n'entre jamais dans le suivi.

`count` est un entier de 3 à 20 ; `difficulty` vaut 1, 2, 3 ou null. Le contenu
est généré une fois et persiste. Aucun ajustement en cours de séance : la
difficulté est adaptée lors de la création de la séance suivante.

Résumé de séance : `id`, `learner_id`, `created_by`, `mode`, `status`,
`created_at`, `completed_at`, `assistance`, `notes`. Statuts : `open`,
`completed`, `cancelled`. Une séance détaillée ajoute `exercices` : chaque
exercice reprend le contrat du générateur sans `bonne_reponse`, avec `skill`
et `answered`. Les solutions sont révélées uniquement après soumission.

La réponse respecte le format du type : chaîne pour l'intrus, entier pour le
dénombrement, dictionnaire mot → correspondant pour l'association. Comparaison
exacte, casse et accents inclus. Les booléens ne sont pas des réponses entières.
`elapsed_seconds` est un nombre fini entre 0 et 86400, déclaré par le client,
conservé mais non utilisé pour noter. Une seule soumission par exercice,
sans écrasement ni rejeu. Toutes les réponses sont requises pour clôturer.

`assistance` est obligatoire : `total`, `partiel`, `allege` ou `autonome`.
`notes` est facultatif, limité à 2 000 caractères. Les séances ouvertes,
abandonnées et d'entraînement n'affectent pas la progression. Les corrections
sont des données à présenter dans l'interface selon les contraintes de stimuli
du projet ; le backend n'impose pas de message sonore ou visuel.

Exemple de création et lecture :

```powershell
$seance = Invoke-RestMethod "$base/learners/$($eleve.id)/sessions" -Headers $headers -Method Post -ContentType 'application/json' -Body '{"mode":"initial","count":3}'
Invoke-RestMethod "$base/sessions/$($seance.id)" -Headers $headers
# Pour chaque exercice, soumettre la réponse de l'élève :
$exercice = $seance.exercices[0]
Invoke-RestMethod "$base/sessions/$($seance.id)/exercises/$($exercice.identifiant)/answers" -Headers $headers -Method Post -ContentType 'application/json' -Body '{"reponse":{"chat":"animal"},"elapsed_seconds":12}'
# Après toutes les réponses :
Invoke-RestMethod "$base/sessions/$($seance.id)/complete" -Headers $headers -Method Post -ContentType 'application/json' -Body '{"assistance":"partiel","notes":"Séance accompagnée"}'
```

La réponse illustrative doit être remplacée par la réponse réelle à l'exercice
tiré ; elle n'est pas nécessairement correcte pour ce tirage.

## Administration

| Méthode et chemin | Entrée | Succès et sortie | Erreurs spécifiques |
| --- | --- | --- | --- |
| GET `/admin/users` | `limit=50`, `offset=0` | 200, liste de comptes publics | 403 hors admin |
| PATCH `/admin/users/{user_id}/status` | `{active:true}` | 200, compte mis à jour | 404 compte absent ; 403 cible administrateur |
| PATCH `/admin/users/{user_id}/role` | `{role:"teacher"}` | 200, compte mis à jour | 404 absent ; 403 conversion élève/adulte ou cible admin ; 422 rôle non public |
| GET `/admin/stats` | Aucun corps | 200, compteurs `users`, `learners`, `sessions`, `session_exercises` | 403 hors admin |

Le premier administrateur est créé localement, avec saisie masquée du mot de
passe. Aucun secret par défaut ni endpoint public de promotion :

```powershell
python -m backend.manage create-admin
python -m backend.manage reset-password
```

La seconde commande permet à l'opérateur du serveur de réinitialiser un mot
de passe après vérification de l'identité hors application ; elle révoque les
jetons existants. Il n'y a pas d'envoi d'email ni de procédure automatisée de
récupération. Une suspension conserve l'historique et invalide les sessions.

## Erreurs communes et configuration

401 : jeton absent, expiré, révoqué ou compte suspendu. 403 : action interdite
pour le rôle courant. 404 : ressource inexistante ou non accessible (les profils
des autres utilisateurs ne sont pas divulgués). 409 : conflit métier.
422 : validation du JSON ou des paramètres. Erreurs métier sous forme
`{"detail":"message"}` ; validation sous forme `{"detail":[...]}`.
204 ne renvoie aucun corps. Horodatages : secondes Unix UTC.

| Variable | Défaut | Usage |
| --- | --- | --- |
| `PLP_DB_PATH` | `backend/data/plp.sqlite3` | Fichier SQLite, créé à la première requête de plateforme |
| `PLP_CORS_ORIGINS` | `http://localhost:5500,http://127.0.0.1:5500` | Origines HTTP autorisées, séparées par des virgules |
| `PLP_MASTERY_SPACING_DAYS` | `1` | Délai positif fini entre deux confirmations de maîtrise |

SQLite conserve les données après redémarrage ; les transactions regroupent
les opérations d'une requête et les clés étrangères assurent les suppressions
en cascade. Les fichiers de base, environnements virtuels et secrets ne sont
pas versionnés. Sauvegarder le fichier SQLite serveur arrêté. Le schéma est
la version initiale de plateforme ; les futures évolutions structurelles
nécessiteront des migrations explicites. Le cache des anciens endpoints de
démonstration reste distinct et non partagé entre workers.

## Vérification et périmètre restant

```powershell
python -m pip install -r backend/requirements-dev.txt
python -B -m unittest backend.test_api backend.test_platform -v
```

Prototype fonctionnel de backend, pas une déclaration de préparation à la
production : le frontend reste à raccorder ; la vérification d'email, les
notifications, les groupes/classes, l'édition de nouveaux modèles d'exercices,
le memory, les médias et les intégrations externes ne sont pas implémentés.
Le serveur doit être déployé derrière HTTPS avant utilisation distante des
jetons. Les accès adultes reposent sur une invitation du responsable et
l'inscription des rôles est déclarative. La base contient des données de
comptes et de suivi : définir avec l'équipe les durées de conservation,
la suppression des comptes et les conditions d'utilisation avant collecte
réelle. La logique floue est explicable mais ses paramètres et la durée de
confirmation doivent être validés par les référents pédagogiques.
