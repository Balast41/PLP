# Moteur de recommandations

## Objectif et statut des règles

Le suivi tient compte du taux de réussite et du niveau d'accompagnement.
Les repères pédagogiques issus des réunions sont : moins de 33 % de réussite,
environ 50 %, plus de 66 % ; nuancer par l'accompagnement ; confirmer les
réussites à distance ; exclure les entraînements libres. Les fonctions
d'appartenance, coefficients, conclusions et le délai d'un jour ci-dessous
sont des hypothèses explicites de prototype à valider, pas des règles fournies
par les référents ni une évaluation clinique.

Implémentation pure Python : `backend/fuzzy.py`. Aucune IA ou API externe.
Le moteur décrit les trois compétences du générateur actuel.

## Entrées et appartenances

Pour chaque séance clôturée, chaque compétence a un taux de réussite
`x = bonnes réponses / nombre de réponses`. Le questionnaire adulte fournit
l'autonomie `y` selon : total = 0,25 ; partiel = 0,5 ; allégé = 0,75 ;
autonome = 1. Le temps est stocké sans intervenir dans la notation.

Pour x et y dans [0,1], les mêmes fonctions sont utilisées :

```text
faible(v) = clip((0.50-v)/0.17, 0, 1)
moyen(v)  = max(0, min((v-0.33)/0.17, (0.66-v)/0.16, 1))
eleve(v)  = clip((v-0.50)/0.16, 0, 1)
```

Ces ensembles se recouvrent, ce qui permet d'activer plusieurs règles.

## Inférence Sugeno d'ordre zéro

Une règle est activée avec `min(degré de réussite, degré d'autonomie)`.
Ses conclusions numériques sont :

| Réussite / autonomie | Faible | Moyenne | Élevée |
| --- | --- | --- | --- |
| Faible | 0,10 | 0,15 | 0,20 |
| Moyenne | 0,25 | 0,45 | 0,55 |
| Élevée | 0,40 | 0,65 | 0,90 |

Le score est la moyenne des conclusions pondérée par leur activation :
`sum(activation * conclusion) / sum(activation)`, arrondie à quatre décimales.
Les appartenances et toutes les règles actives sont retournées dans
`inference`, pour expliquer la décision. Par exemple, 100 % de réussite avec
accompagnement total produit 0,40, tandis que 70 % en autonomie produit 0,90.

## État d'une compétence

Seules les séances clôturées `initial` et `evaluated` sont traitées dans
l'ordre chronologique. Les séances `practice` et les séances abandonnées ou
ouvertes sont ignorées. Le score courant est celui de la dernière séance
éligible pour cette compétence : ce choix donne du poids à la situation
récente, et ne prétend pas constituer un modèle longitudinal validé.

- Aucune séance éligible : `non_evalue`, niveau recommandé 2 (départ ambitieux).
- Score < 0,33 : `non_validee`, niveau 1.
- 0,33 ≤ score < 0,66 : `en_apprentissage`, niveau 2.
- Score ≥ 0,66 : `a_confirmer`, niveau 3.
- Deux confirmations ≥ 0,66 espacées du délai configuré : `validee`, niveau 3.

Le délai est `PLP_MASTERY_SPACING_DAYS`, un jour par défaut. Plusieurs réussites
le même jour ne suffisent pas. Une séance ultérieure dont le score est inférieur
à 0,66 réinitialise les confirmations. Une compétence peut donc redevenir
`en_apprentissage` ou `non_validee` après une difficulté ultérieure.

## Recommandation

L'évaluation initiale répartit les questions sur toutes les compétences, au
niveau 2 par défaut. Ensuite les recommandations sont limitées aux compétences
du plan courant, avec priorité aux compétences non évaluées, puis au score
le plus faible. Si aucune préférence n'est fournie à la création d'une séance,
le backend choisit cette compétence et sa difficulté recommandée.

L'utilisateur lié peut choisir un autre type parmi ceux autorisés par le
plan ; seuls un enseignant lié ou un administrateur peuvent changer les
compétences prévues. La difficulté et le nombre d'exercices sont fixés lors
de la création ; il n'y a pas encore d'adaptation de longueur en temps réel.
Une compétence validée reste disponible pour s'entraîner en mode `practice`.

## Tests et ajustements

Les tests vérifient les frontières des appartenances, la pondération de
l'autonomie, la confirmation espacée et l'exclusion des entraînements.
Toute modification des règles dans `fuzzy.py` doit être accompagnée d'une
mise à jour de ce document et de cas de référence pédagogiques approuvés.
