# Explications du projet ApprenTSAge

Le travail a été réalisé en deux étapes : un générateur d'exercices autonome,
puis un backend FastAPI pour les comptes, les élèves, les séances et leur
suivi. Le code est sur la branche `vapor214/backend-fastapi`. Cette branche
n'a pas été fusionnée dans `main` dans le cadre de ce travail.

Ce document présente ce qui fonctionne et ce qui reste à faire. Le backend
est fonctionnel comme prototype ; l'interface existante n'y est pas encore
raccordée et aucun déploiement public n'a été réalisé.

## 1. Le générateur d'exercices

Le générateur utilise de petites listes de données écrites dans le code.
Il fonctionne localement, sans IA externe, service payant ou dépendance externe.
Il ne lit pas les PDF pendant son fonctionnement et ne reproduit pas leurs
illustrations : les familles du MVP sont inspirées de leur classement.

Trois familles sont disponibles :

| Type | Principe |
| --- | --- |
| Association | Relier des mots à une catégorie ou à un élément associé |
| Intrus | Trouver le mot qui n'appartient pas à la même famille |
| Dénombrement | Compter des éléments représentés textuellement |

La fonction `generate_exercise(type=None, difficulty=1)` retourne un dictionnaire
sérialisable en JSON : identifiant, type, difficulté, énoncé, propositions et
bonne réponse. Sans type demandé, elle choisit une famille au hasard.

Trois niveaux font varier le nombre de propositions ou la quantité à compter.
Les identifiants sont uniques en pratique grâce aux UUID, mais les contenus
peuvent se répéter : ils proviennent d'un petit catalogue statique.

Le module est dans `generateur/exercise_generator.py`. Le script
`generateur/demo_exercises.py` produit cinq exercices et vérifie leur structure,
leur sérialisation et la cohérence des propositions avec les réponses.

## 2. Le rôle du backend FastAPI

Le backend reçoit les demandes de l'interface et applique les règles de la
plateforme. Une adresse appelée endpoint correspond à une action : créer un
compte, préparer une séance ou enregistrer une réponse, par exemple.
Les échanges se font en JSON.

Un parcours typique est : connexion de l'adulte, sélection d'un élève,
préparation d'une séance, réponses aux exercices, déclaration de
l'accompagnement, puis consultation de la progression et des recommandations.

FastAPI reçoit les requêtes. Pydantic vérifie les données et décrit les
contrats d'entrée et de sortie. Uvicorn lance le serveur HTTP.
Les modules sont séparés pour les routes, les modèles de données, la sécurité,
le stockage et la logique floue. Les erreurs sont renvoyées avec un code HTTP
et un champ `detail` décrivant le problème.

## 3. Les comptes et la connexion

Le backend permet l'inscription, la connexion, la déconnexion, la consultation
du compte connecté, la modification du nom affiché et le changement du mot de
passe.

Quatre rôles publics sont disponibles : élève, enseignant, parent et
accompagnant. Le rôle élève s'appelle `child` dans le code, mais peut désigner
une personne de tout âge. Le rôle administrateur n'est pas accessible à
l'inscription publique.

Les mots de passe sont transformés avec scrypt et un sel aléatoire : ils ne
sont pas enregistrés en clair. Ils doivent contenir entre 12 et 128 caractères.
Les adresses email sont normalisées en minuscules et contrôlées syntaxiquement,
sans vérification de la boîte mail.

La connexion produit un jeton valable douze heures. L'interface doit le
présenter dans l'en-tête `Authorization: Bearer ...` pour les routes protégées.
Seule une empreinte du jeton est stockée. Il est révocable ; il ne s'agit pas
d'un JWT. Après expiration, il faut se reconnecter : aucun refresh token n'est
implémenté.

Cinq échecs de connexion pour une adresse déclenchent un blocage de quinze
minutes. La déconnexion révoque le jeton courant. Un changement de mot de
passe, une suspension ou une modification de rôle révoque toutes les sessions
du compte concerné.

## 4. Les profils élèves et les accès

Un compte de connexion et un profil élève sont distincts. Un adulte peut
créer un profil, renseigner son nom et sa préférence audio. Il en devient
responsable et peut inviter d'autres personnes à y accéder.

Les invitations visent une adresse email précise, expirent après 48 heures
et ne sont utilisables qu'une fois. Le responsable transmet lui-même le jeton :
aucun email automatique n'est envoyé. Le destinataire se connecte avec le
compte correspondant à l'adresse invitée, puis accepte l'invitation.
Un compte élève ne peut être rattaché qu'à un seul profil.

Un accès peut être retiré immédiatement. Connaître un identifiant ne suffit
pas pour consulter un dossier. Les administrateurs ont accès à tous les profils ;
les autres utilisateurs doivent être explicitement liés.

Les adultes liés peuvent modifier le nom et la préférence audio. Le responsable
ou un administrateur peut supprimer le profil : cette suppression efface aussi
ses liens, invitations, compétences prévues, séances et résultats.

## 5. Le programme pédagogique

Trois compétences correspondent au catalogue actuel :

| Compétence | Type d'exercice |
| --- | --- |
| Vocabulaire | Association |
| Catégorisation | Intrus |
| Numération | Dénombrement |

Chaque profil possède une liste de compétences à travailler. Les trois sont
activées à sa création. Seul un enseignant lié ou un administrateur peut
modifier cette liste. Un parent ou un accompagnant peut choisir un type parmi
les compétences prévues, sans changer les objectifs pédagogiques.

La modification du programme ne change pas les séances déjà créées : leur
contenu reste figé. L'évaluation initiale constitue un cas particulier : elle
couvre les trois compétences, même si le programme courant est plus restreint.

## 6. Les séances, les réponses et l'accompagnement

Trois modes existent :

- `initial` : évaluation initiale des trois compétences, au niveau 2 par défaut.
- `evaluated` : séance comptant dans le suivi, après une évaluation initiale terminée.
- `practice` : entraînement libre, disponible dès le début, exclu de la progression.

Une séance contient entre trois et vingt exercices. Le contenu est généré une
fois, puis enregistré. Il est possible de lister, reprendre, terminer ou
abandonner les séances. Une séance est ouverte, terminée ou abandonnée.

Les solutions restent sur le serveur jusqu'à la soumission d'une réponse.
Une réponse est vérifiée, conservée et accompagnée de sa correction. Une
seconde soumission au même exercice est refusée, afin de conserver le résultat
initial. La comparaison est exacte : casse et accents comptent dans les mots.

Toutes les réponses sont nécessaires pour terminer une séance. Un adulte lié
doit renseigner l'accompagnement : total, partiel, allégé ou autonome. Il peut
ajouter des notes. L'élève ne peut pas attester lui-même ce niveau d'aide.

Le temps de réponse peut être enregistré, mais il est déclaré par le client
et n'intervient pas dans la notation. Les corrections ne déclenchent aucun
son ou affichage par elles-mêmes : leur présentation appartient au frontend.

## 7. La logique floue et les recommandations

L'objectif est de nuancer le taux de bonnes réponses selon l'accompagnement.
Réussir avec une aide totale ne doit pas avoir le même poids que réussir en
autonomie.

Le moteur combine le taux de réussite et une valeur d'autonomie correspondant
à l'aide déclarée. Il utilise trois catégories qui se chevauchent : faible,
moyen et élevé. Neuf règles combinent les deux entrées et produisent un score
entre 0 et 1. Cette méthode est une inférence Sugeno d'ordre zéro.

Le résultat expose aussi les degrés d'appartenance et les règles activées :
la décision peut être expliquée. Par exemple, avec les coefficients actuels,
100 % de réussite sous accompagnement total produit un score de 0,40, tandis
que 70 % en autonomie produit 0,90.

Les états sont : non évalué, non validé, en apprentissage, à confirmer et validé.
La validation demande au moins deux confirmations suffisamment espacées :
un jour par défaut. Une difficulté ultérieure peut remettre cette validation
en question. Le score courant repose sur la dernière séance éligible pour la
compétence, pas sur la moyenne de tout l'historique.

Les séances ouvertes, abandonnées et les entraînements libres sont exclus
du suivi. Les recommandations privilégient les compétences non évaluées,
puis les moins maîtrisées, en respectant le programme courant. Elles proposent
aussi une difficulté pour la prochaine séance. Sans préférence explicite,
la création d'une séance utilise ce choix.

Les coefficients, fonctions d'appartenance, conclusions et délai d'un jour
sont des hypothèses de prototype à valider pédagogiquement. Ce n'est pas une
évaluation clinique. La difficulté est adaptée entre les séances, pas pendant
une séance. Les détails se trouvent dans [la documentation du moteur](backend/LOGIQUE_FLOUE.md).

## 8. La base de données et l'administration

Une base SQLite locale conserve les comptes, empreintes des jetons, profils,
accès, invitations, programmes, séances et réponses après redémarrage.
Des transactions regroupent les opérations d'une requête ; les clés étrangères
assurent les suppressions en cascade prévues.

L'administration permet de lister les comptes, les suspendre ou les réactiver,
modifier certains rôles adultes et consulter les nombres de comptes, profils,
séances et exercices enregistrés. Une suspension conserve l'historique.
Les conversions élève/adulte et la gestion des administrateurs ne sont pas
autorisées par l'endpoint de modification des rôles.

Deux commandes locales sont disponibles :

```powershell
python -m backend.manage create-admin
python -m backend.manage reset-password
```

Le mot de passe est saisi de façon masquée. Aucun compte administrateur ou
secret par défaut n'est créé. La réinitialisation exige une vérification de
l'identité hors application par l'opérateur ; elle ne remplace pas une
procédure automatique de récupération par email.

Les anciennes routes de démonstration des exercices restent accessibles sans
compte. Elles utilisent un cache séparé de 1 000 exercices, perdu au redémarrage,
et ne modifient jamais la progression des élèves.

## 9. Lancement et configuration

Depuis la racine du dépôt :

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Le serveur est disponible sur `http://127.0.0.1:8000`. Python 3.10 minimum est
nécessaire. Les dépendances serveur sont FastAPI, Pydantic et Uvicorn ; HTTPX
est ajouté pour les tests.

Trois variables configurent le prototype :

| Variable | Utilité | Défaut |
| --- | --- | --- |
| `PLP_DB_PATH` | Emplacement de SQLite | `backend/data/plp.sqlite3` |
| `PLP_CORS_ORIGINS` | Origines autorisées à appeler l'API depuis le navigateur | `http://localhost:5500,http://127.0.0.1:5500` |
| `PLP_MASTERY_SPACING_DAYS` | Délai entre confirmations de maîtrise | `1` jour |

Les bases locales et environnements virtuels sont exclus de Git. Le schéma
SQLite est une première version ; ses futures modifications structurelles
nécessiteront des migrations. Le cache de démonstration n'est pas partagé
entre processus, contrairement au fichier de base utilisé pour la plateforme.

## 10. Documentation et vérifications

Chaque endpoint dispose d'une documentation des entrées, sorties, permissions
et erreurs. Swagger dans `/docs` permet de les essayer. `/redoc` permet de
lire les contrats et `/openapi.json` fournit leur description machine.

Les 19 tests automatisés ont passé lors de la vérification du backend. Ils
couvrent la génération, les contrats, les comptes, les droits, les invitations,
les séances, les corrections, la persistance, l'expiration des jetons et la
progression. Ils ne prouvent pas une validation pédagogique ou une préparation
complète à la production.

```powershell
python -m pip install -r backend/requirements-dev.txt
python -B -m unittest backend.test_api backend.test_platform -v
```

Documents associés : [guide des requêtes](Requetes_types.md),
[documentation technique](backend/PLATEFORME.md) et
[guide des exercices de démonstration](backend/README.md).

## 11. Ce qui reste à faire

- Raccorder l'interface au backend : les formulaires existants restent en démonstration.
- Déployer le serveur ; aucun hébergement public n'a été mis en place ici.
- Vérifier les emails et les qualifications des rôles adultes, actuellement déclaratifs.
- Ajouter les notifications, la récupération automatique des mots de passe et la suppression des comptes.
- Développer les classes/groupes, l'édition de nouveaux modèles, le memory et les médias.
- Produire la lecture audio : seule la préférence est actuellement enregistrée.
- Ajouter une éventuelle adaptation de longueur en cours de séance.
- Valider les règles pédagogiques et les paramètres du moteur flou avec les référents.
- Définir la conservation, la suppression et les conditions d'utilisation des données avant une collecte réelle.

Une utilisation distante doit notamment protéger les échanges par HTTPS.
Le résultat actuel est un backend fonctionnel de prototype, pas encore une
plateforme complète prête à accueillir de vrais utilisateurs en production.
