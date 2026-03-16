"""
main.py - Point d'entrée principal du projet TrueSkill
========================================================
Lance la simulation complète :
  1. Création de 10 joueurs avec compétences cachées aléatoires
  2. Simulation de 200 matchs 1v1
  3. Génération des graphes de convergence µ et σ
  4. Affichage du classement final
  5. Export des résultats en CSV

Utilisation :
    cd groupe-02-trueskill-matchmaking/
    python src/main.py
"""

import sys
import os
import random
import pandas as pd

# Ajout du dossier src au path Python pour les imports relatifs
sys.path.insert(0, os.path.dirname(__file__))

from simulation import creer_joueurs, simuler_tournoi, classement_final
from matchmaking import probabilite_victoire, qualite_match
from visualisation import (
    graphe_convergence_mu,
    graphe_convergence_sigma,
    graphe_classement_final,
    graphe_mu_individuel,
)

# ─────────────────────────────────────────────
# PARAMÈTRES DE LA SIMULATION
# ─────────────────────────────────────────────
NB_JOUEURS = 10       # Nombre de joueurs dans la simulation
NB_MATCHS = 200       # Nombre de matchs à simuler
GRAINE = 42           # Graine aléatoire pour reproductibilité
DOSSIER_DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def afficher_joueurs(joueurs):
    """Affiche les joueurs avec leur compétence cachée initiale."""
    print("\n" + "=" * 55)
    print("  JOUEURS CRÉÉS (compétences cachées)")
    print("=" * 55)
    print(f"  {'Joueur':<15} {'Compétence cachée':>20}")
    print("-" * 55)
    for j in joueurs:
        print(f"  {j['nom']:<15} {j['competence']:>20.2f}")
    print("=" * 55)


def afficher_classement(joueurs_classes):
    """Affiche le classement final TrueSkill."""
    print("\n" + "=" * 65)
    print("  CLASSEMENT FINAL TRUESKILL")
    print("=" * 65)
    print(f"  {'Rang':<5} {'Joueur':<15} {'µ':>8} {'σ':>8} {'Score(µ-3σ)':>12} {'Vrai niveau':>12}")
    print("-" * 65)
    for rang, j in enumerate(joueurs_classes, start=1):
        score = j['rating'].mu - 3 * j['rating'].sigma
        print(
            f"  {rang:<5} {j['nom']:<15} "
            f"{j['rating'].mu:>8.2f} "
            f"{j['rating'].sigma:>8.2f} "
            f"{score:>12.2f} "
            f"{j['competence']:>12.2f}"
        )
    print("=" * 65)


def exporter_csv(joueurs_classes, historique, dossier):
    """Exporte les résultats en CSV dans le dossier data/."""
    os.makedirs(dossier, exist_ok=True)

    # CSV 1 : Classement final
    donnees_classement = []
    for rang, j in enumerate(joueurs_classes, start=1):
        donnees_classement.append({
            'rang': rang,
            'joueur': j['nom'],
            'mu_final': round(j['rating'].mu, 4),
            'sigma_final': round(j['rating'].sigma, 4),
            'score_conservateur': round(j['rating'].mu - 3 * j['rating'].sigma, 4),
            'competence_reelle': round(j['competence'], 4),
        })
    df_classement = pd.DataFrame(donnees_classement)
    chemin1 = os.path.join(dossier, "classement_final.csv")
    df_classement.to_csv(chemin1, index=False)
    print(f"  [OK] Classement exporté : {chemin1}")

    # CSV 2 : Historique des matchs
    df_matchs = pd.DataFrame(historique)
    chemin2 = os.path.join(dossier, "historique_matchs.csv")
    df_matchs.to_csv(chemin2, index=False)
    print(f"  [OK] Historique des matchs exporté : {chemin2}")


def main():
    """Fonction principale : orchestre toute la simulation."""

    print("\n" + "█" * 55)
    print("  PROJET TRUESKILL - ECE Paris ING4 Groupe 02")
    print("  Simulation de matchmaking compétitif")
    print("█" * 55)

    # ── 1. Reproductibilité ──────────────────────────────────
    random.seed(GRAINE)
    print(f"\n[INFO] Graine aléatoire : {GRAINE} (résultats reproductibles)")

    # ── 2. Création des joueurs ──────────────────────────────
    print(f"\n[ÉTAPE 1] Création de {NB_JOUEURS} joueurs...")
    joueurs = creer_joueurs(nb_joueurs=NB_JOUEURS, mu_min=10, mu_max=50)
    afficher_joueurs(joueurs)

    # ── 3. Simulation du tournoi ─────────────────────────────
    print(f"\n[ÉTAPE 2] Simulation de {NB_MATCHS} matchs 1v1...")
    historique = simuler_tournoi(joueurs, nb_matchs=NB_MATCHS)
    print(f"  [OK] {len(historique)} matchs simulés.")

    # Aperçu des 5 premiers matchs
    print("\n  Aperçu des 5 premiers matchs :")
    print(f"  {'Match':<7} {'Joueur 1':<15} {'Joueur 2':<15} {'Résultat'}")
    print("  " + "-" * 50)
    for m in historique[:5]:
        gagnant = m['joueur1'] if m['resultat'] == 'joueur1' else m['joueur2']
        print(f"  {m['match_num']:<7} {m['joueur1']:<15} {m['joueur2']:<15} → {gagnant} gagne")

    # ── 4. Classement final ──────────────────────────────────
    print(f"\n[ÉTAPE 3] Calcul du classement final...")
    joueurs_classes = classement_final(joueurs)
    afficher_classement(joueurs_classes)

    # ── 5. Probabilités de victoire entre les tops ───────────
    print("\n[INFO] Probabilités de victoire (top 3 vs bottom 3) :")
    top = joueurs_classes[:3]
    bot = joueurs_classes[-3:]
    for j1 in top[:1]:
        for j2 in bot[:1]:
            prob = probabilite_victoire(j1, j2)
            print(f"  P({j1['nom']} bat {j2['nom']}) = {prob:.1%}")
            print(f"  Qualité du match = {qualite_match(j1, j2):.3f} (1.0 = parfaitement équilibré)")

    # ── 6. Génération des graphes ────────────────────────────
    print(f"\n[ÉTAPE 4] Génération des graphes...")
    graphe_convergence_mu(joueurs, dossier_sortie=DOSSIER_DATA)
    graphe_convergence_sigma(joueurs, dossier_sortie=DOSSIER_DATA)
    graphe_classement_final(joueurs_classes, dossier_sortie=DOSSIER_DATA)

    # Graphe individuel pour le joueur classé 1er
    graphe_mu_individuel(joueurs_classes[0], dossier_sortie=DOSSIER_DATA)
    print(f"  [OK] Graphe individuel pour {joueurs_classes[0]['nom']}")

    # ── 7. Export CSV ────────────────────────────────────────
    print(f"\n[ÉTAPE 5] Export des résultats en CSV...")
    exporter_csv(joueurs_classes, historique, dossier=DOSSIER_DATA)

    # ── Conclusion ───────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  SIMULATION TERMINÉE AVEC SUCCÈS")
    print(f"  Graphes et CSV disponibles dans : {os.path.abspath(DOSSIER_DATA)}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
