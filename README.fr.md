# MOTOR v5.0.1 — probabilité d'entrée en récession aux États-Unis

[English](README.md) · [Español](README.es.md) · [中文](README.zh-CN.md) · **Français** · [Dansk](README.da.md)

[![tests](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml/badge.svg)](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml)

## De quoi s'agit-il

MOTOR estime la probabilité qu'une récession américaine, datée par le NBER, **commence au cours des quatre
prochains trimestres**. Le modèle opérationnel n'utilise qu'une seule variable : la courbe des taux (rendement du
Trésor à 10 ans moins le bon à 3 mois), dans une régression logistique avec pénalité L2. Tout est validé par un
*walk-forward* purgé à origine croissante : à chaque date historique, le modèle ne voit que ce qui était connu à
ce moment-là. Seules des données gratuites sont utilisées (FRED, Réserve fédérale, Shiller), et chaque instantané
de données est conservé avec son empreinte (hash).

## Comment il reste honnête

- **Un registre prospectif** ([LOG.md](LOG.md)) : chaque mois, une lecture est enregistrée *avant* que le
  résultat soit connu, et les lignes ne sont jamais modifiées. Les règles de notation ont été publiées avant la
  quatrième ligne.
- **La lecture est toujours comparée au taux de base** (la fréquence historique à laquelle une récession a
  commencé dans l'année, environ 18 %). Si l'incertitude du modèle inclut le taux de base, le verdict est
  « indiscernable du taux de base ».
- **Les échecs sont publiés aussi** : sept variables candidates ont été testées et rejetées, et figurent à côté du
  modèle qui a survécu.
- **Des chiffres avec leur incertitude** : l'amélioration de la log-loss par rapport au taux de base est de
  +20,4 % (sans oracle, 219 origines), mais son intervalle à 90 % commence sous zéro. Détecter cet avantage avec
  une puissance de 80 % exigerait de l'ordre de 150 ans de registre.
- **Un conseil de modèles de langage** débat et ratifie chaque changement de méthode ; les décisions sont scellées
  avant l'écriture du code ([RAADETS_SPEC7.md](RAADETS_SPEC7.md) et précédents).

## Lecture actuelle

Dernière lecture enregistrée (2026-10-10) : **P = 15,1 %** [10,4–21,6 %] contre un taux de base de 18,0 %, soit
indiscernable du taux de base. Une lecture intermédiaire du 2026-10-27 (non enregistrée) donnait 14,8 %. Le
modèle ne lit que le niveau de la courbe et ne voit pas les chocs extérieurs : ce chiffre signifie « autour du
taux de base », pas « risque faible ».

## Pour en savoir plus

La documentation complète en anglais se trouve dans [README.md](README.md). La documentation technique détaillée,
le code et le registre sont en danois ; les textes opératoires du conseil sont en anglais. La page
[dashboard.html](dashboard.html) affiche la lecture actuelle.

Code sous licence MIT ; textes propres sous CC BY 4.0 ; les données de tiers ont leurs propres conditions (voir
[NOTICE.md](NOTICE.md)). Le modèle n'est ni un signal de trading ni un conseil en investissement.
