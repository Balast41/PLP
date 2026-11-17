"""Inférence Sugeno explicable, sans bibliothèque externe.

Ces règles sont des hypothèses de prototype, pas un diagnostic clinique.
"""

SKILLS = {'vocabulaire': 'association', 'categorisation': 'intrus', 'numeration': 'denombrement'}
ASSISTANCE = {'total': .25, 'partiel': .5, 'allege': .75, 'autonome': 1.0}


def memberships(value: float) -> dict[str, float]:
    return {
        'faible': max(0., min(1., (.5 - value) / .17)),
        'moyen': max(0., min((value - .33) / .17, (.66 - value) / .16, 1.)),
        'eleve': max(0., min(1., (value - .5) / .16)),
    }


def infer(success: float, autonomy: float) -> dict:
    if not 0 <= success <= 1 or not 0 <= autonomy <= 1:
        raise ValueError('Entrées attendues entre 0 et 1.')
    performance = memberships(success)
    independence = memberships(autonomy)
    # Colonnes : autonomie faible, moyenne, élevée. Lignes : réussite idem.
    outputs = ((.1, .15, .2), (.25, .45, .55), (.4, .65, .9))
    rules = []
    for i, (level, degree) in enumerate(performance.items()):
        for j, (autonomy_level, autonomy_degree) in enumerate(independence.items()):
            weight = min(degree, autonomy_degree)
            if weight:
                rules.append({'reussite': level, 'autonomie': autonomy_level,
                              'activation': round(weight, 6), 'conclusion': outputs[i][j]})
    score = sum(r['activation'] * r['conclusion'] for r in rules) / sum(r['activation'] for r in rules)
    return {'score': round(score, 4), 'appartenances_reussite': performance,
            'appartenances_autonomie': independence, 'regles': rules}


def skill_progress(rows: list[dict], spacing_days: float = 1) -> dict:
    eligible = [r for r in rows if r['mode'] != 'practice']
    if not eligible:
        return {'etat': 'non_evalue', 'score': None, 'seances': 0, 'confirmations': 0, 'difficulty': 2, 'inference': None}
    evaluations = [infer(r['success'], ASSISTANCE[r['assistance']]) for r in eligible]
    last = evaluations[-1]
    confirmations = 0
    last_confirmation = None
    # Une faiblesse ultérieure réinitialise la confirmation de maîtrise.
    for row, evaluation in zip(eligible, evaluations):
        if evaluation['score'] < .66:
            confirmations, last_confirmation = 0, None
        elif last_confirmation is None or row['completed_at'] - last_confirmation >= spacing_days * 86400:
            confirmations += 1
            last_confirmation = row['completed_at']
    score = last['score']
    state = 'validee' if confirmations >= 2 else 'a_confirmer' if score >= .66 else 'non_validee' if score < .33 else 'en_apprentissage'
    return {'etat': state, 'score': score, 'seances': len(eligible), 'confirmations': confirmations,
            'difficulty': 3 if score >= .66 else 2 if score >= .33 else 1,
            'inference': last}
