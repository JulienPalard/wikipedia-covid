"""Uses https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
- donnees-hospitalieres-covid19
- donnees-hospitalieres-nouveaux-covid19

This scripts downloads data from data.gouv.fr and prints a partial
Wikipedia page with some graphs.
"""

from collections import defaultdict
from datetime import datetime
from dateutil.parser import parse
from io import StringIO
from statistics import mean
from typing import Dict
import csv
import locale

import requests

csv.register_dialect("datagouv", delimiter=";")

locale.setlocale(locale.LC_ALL, "C")


def wiki_date(date):
    """I have no idea how graph dates should be written on Wikipedia,
    so I use what I see, this code may be ugly.
    """
    if not isinstance(date, datetime):
        return date
    month = date.strftime("%b").replace("Jun", "June").replace("Sep", "Sept")
    return f"{int(date.day)} {month}"


LEGEND_COMMENT = """
<!--UNE LÉGENDE N'A PAS VOCATION À ÊTRE ACTUALISÉE, cela pour une raison simple : à la fin de l'épidémie, en adoptant une légende avec pour exemple le jour actuel, on arrive à une situation où la grande majorité des légendes des graphiques seront à 0. Une donnée stable doit être laissé dans la lecture : celle qui correspond au pic. Si le pic du graphique change, il est possible d'actualiser la lecture. Mais sinon, il ne faut pas remplacer la donnée de la lecture par une donnée éphémère. -->"""


def wiki_graph(
    x,
    y,
    title,
    lecture="",
    xAxisTitle="",
    y1Title="",
    legend="",
    colors="#f6b4b4, #bb8033",
):
    x = [wiki_date(item) for item in x]
    y = list(y)
    if not xAxisTitle:
        xAxisTitle = title
    if y1Title:
        y1Title = f"|y1Title={y1Title}"
    if lecture:
        lecture = f"Lecture : {lecture}"
    print(
        f"""{{|
|-
| width="400" | '''''{title}'''''
|-
|{{{{Graph:Chart
|type=line
|colors={colors}
|linewidth=1
|showSymbols=1
|width=700
|showValues=
|xAxisTitle={xAxisTitle}
|xType=date
|xAxisAngle=-60
| x = {", ".join(x)}
| y = {", ".join(str(v) for v in y)}
{y1Title}
|yGrid= |xGrid=
}}}}
{lecture}
|}}

""".replace(
            "\n\n", "\n"
        )
    )


def compute_variation(by_day: Dict[str, int]) -> Dict[str, int]:
    """Given dict, compute for each value the difference with the previous value."""
    return dict(
        zip(
            list(by_day.keys())[1:],
            [
                current - last
                for last, current in zip(by_day.values(), list(by_day.values())[1:])
            ],
        )
    )


def positivite():
    by_day = defaultdict(int)
    with open("sp-pos-quot-fra-2020-09-03-19h15.csv") as csvfile:
        reader = csv.DictReader(csvfile, dialect="datagouv")
        for row in reader:
            by_day[parse(row["jour"])] += int(row["P"])
    by_day = dict(by_day)
    return by_day, compute_variation(by_day)


def donnees_hospitalieres_covid19(column="rea"):
    by_day = defaultdict(int)
    csvfile = StringIO(
        requests.get(
            "https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7"
        ).text
    )
    reader = csv.DictReader(csvfile, dialect="datagouv")
    for row in reader:
        if row["sexe"] != "0":  # specific
            continue
        by_day[parse(row["jour"])] += int(row[column])
    by_day = dict(by_day)
    return by_day, compute_variation(by_day)


def donnees_hospitalieres_nouveau_covid19(column="incid_rea"):
    by_day = defaultdict(int)
    csvfile = StringIO(
        requests.get(
            "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"
        ).text
    )
    reader = csv.DictReader(csvfile, dialect="datagouv")
    for row in reader:
        by_day[parse(row["jour"])] += int(row[column])
    return by_day, compute_variation(by_day)


def hospitalisations():
    print("=== Hospitalisations ===")

    by_day, daily_var = donnees_hospitalieres_covid19("hosp")
    wiki_graph(
        by_day.keys(),
        by_day.values(),
        title="Nombre d'hospitalisations de personnes atteintes de Covid-19",
        xAxisTitle=" Nombre total d’hospitalisations en cours attribués à la Covid-19",
        y1Title="Hospitalisations en cours",
        lecture="le 5 octobre 2020, {{nombre|7294|personnes}} atteintes de Covid-19 étaient hospitalisées.",
    )

    wiki_graph(
        daily_var.keys(),
        daily_var.values(),
        "Variation journalière du nombre d'hospitalisations de personnes atteintes de Covid-19",
        lecture="le 5 octobre 2020, {{nombre|312|personnes}} de plus que la veille sont hospitalisées pour Covid-19. Le nombre de sorties de l'hôpital (pour amélioration ou décès) est soustraites du nombre d'entrées. À ne pas confondre avec le nombre de nouvelles personnes admises quotidiennement qui est donné ci-dessous.",
        xAxisTitle="Variation journalière des hospitalisations attribués à la Covid-19",
        y1Title="Variation journalière des hospitalisations",
    )

    by_day, daily_var = donnees_hospitalieres_nouveau_covid19("incid_hosp")
    wiki_graph(
        by_day.keys(),
        by_day.values(),
        "Nombre quotidien de personnes nouvellement hospitalisées pour Covid-19",
        y1Title="Nombre quotidien de nouvelles hospitalisations",
        xAxisTitle="Nombre quotidien de nouvelles hospitalisations attribués à la Covid-19",
    )


def reanimation():
    print("=== Réanimations ===")
    by_day, daily_var = donnees_hospitalieres_covid19("rea")
    wiki_graph(
        by_day.keys(),
        by_day.values(),
        "Nombre de personnes en réanimation ou soins intensifs pour la Covid-19",
        lecture="Le {{date-|5 octobre 2020}}, {{unité|1415 personnes}} sont en réanimation ou en soins intensifs dans les hôpitaux d'une cause attribuée à la Covid-19."
        + LEGEND_COMMENT,
    )
    wiki_graph(
        daily_var.keys(),
        daily_var.values(),
        "Variation du nombre de personnes en réanimation ou en soins intensifs pour la Covid-19",
        lecture="Le {{date-|5 octobre 2020}}, {{nombre|74 personnes}} de plus que la veille sont en réanimation ou en soins intensifs attribués à la Covid-19. Le nombre de sorties du service de réanimation (pour amélioration ou décès) sont soustraites du nombre d'entrées. À ne pas confondre avec le nombre de nouvelles personnes admises qui est donné ci-dessous."
        + LEGEND_COMMENT,
    )

    by_day, daily_var = donnees_hospitalieres_nouveau_covid19("incid_rea")
    wiki_graph(
        by_day.keys(),
        by_day.values(),
        "Nombre de nouvelles admissions en réanimation dans les hôpitaux",
        lecture="Le {{date-|5 octobre 2020}}, {{nombre|152 personnes}} supplémentaires sont entrées en réanimation à l'hôpital."
        + LEGEND_COMMENT,
    )


def retour_a_domicile():
    print("=== Retours à domicile après hospitalisation ===")
    by_day, daily_var = donnees_hospitalieres_nouveau_covid19("incid_rad")
    wiki_graph(
        by_day.keys(),
        by_day.values(),
        "Nombre cumulé de patients ayant été hospitalisés pour cause de Covid-19 et de retour à domicile en raison de l'amélioration de leur état de santé<ref>[https://dashboard.covid19.data.gouv.fr/ Banque de données gouvernementales sur la Covid-19 en France].</ref>.",
        xAxisTitle="Nombre cumulé de sorties d’hôpital",
        colors="#79BE79, #bb8033",
        y1Title="Sortis d’hôpital",
        lecture="entre le début du recensement et le {{date-|10 mai 2020}}, {{unité|56217 patients}} ont quitté l'hôpital, ils sont retournés à leur domicile en raison de l'amélioration de leur état de santé et selon les critères définis par Haut Conseil de la santé publique ; ils doivent cependant rester confinés jusqu'à guérison complète<ref>[https://sante.journaldesfemmes.fr/fiches-maladies/2621211-coronavirus-isolement-domicile-hotel-quarantaine-guerison-quatorzaine/#coronavirus-retour-domicile-guerison Covid-19 et isolement à domicile : les consignes jusqu'à la guérison] Le Journaldesfemmes, 2 juin 2020</ref>{{,}}<ref>[https://www.hcsp.fr/Explore.cgi/Telecharger?NomFichier=hcspa20200316_corsarcovcriclidesordisodespatin.pdf Avis relatif aux critères cliniques de sortie d’isolement des patients ayant été infectés par le SARS-CoV-2] HCSP, 16 mars 2020</ref>"
        + LEGEND_COMMENT,
    )


def deces_en_hopital_et_ems():
    """WIP"""
    print("==== Décès en hôpital et établissements sociaux ou médico-sociaux ====")
    by_day, daily_var = donnees_hospitalieres_nouveau_covid19("incid_dc")

    wiki_graph(
        by_day.keys(),
        by_day.values(),
        "Nombre total cumulé de décès à l'hôpital attribués à la Covid-19",
        xAxisTitle="Nombre total de décès attribués à la Covid-19 à l’hôpital",
    )


hospitalisations()
reanimation()
retour_a_domicile()
