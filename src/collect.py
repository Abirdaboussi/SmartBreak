"""Étape 1 du pipeline - COLLECTE.

Appelle la source configurée, gère les erreurs d'accès et enregistre la
réponse BRUTE (non modifiée) dans data/raw/<source>/, avec un fichier de
métadonnées (source, URL, date de collecte, run_id, taille).

Implémenté à l'étape 1.4.
"""
