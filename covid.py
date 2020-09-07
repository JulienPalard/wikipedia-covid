#!/usr/bin/env python3

# Uses https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
# - donnees-hospitalieres-covid19
# - donnees-hospitalieres-nouveaux-covid19

import csv
from statistics import mean
from itertools import groupby
from dateutil.parser import parse
import locale
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict

csv.register_dialect("datagouv", delimiter=";")

locale.setlocale(locale.LC_ALL, "fr_FR")

CURRENT_WEEK = date.today().strftime("%Y S%W")


def wiki_graph(title, x, y):
    print()
    print("##", title)
    print()
    x = [d + "(partielle)" if d == CURRENT_WEEK else d for d in x]
    print("| x =", ", ".join(x))
    print("| y = ", ", ".join(str(v) for v in y))
    print()


def analyze_data(by_day, aggregation=sum):
    daily_variation = dict(
        zip(
            list(by_day.keys())[1:],
            [
                current - last
                for last, current in zip(by_day.values(), list(by_day.values())[1:])
            ],
        )
    )

    by_week = {}
    for week, values in groupby(
        by_day.items(), key=lambda kvp: kvp[0].strftime("%Y S%W")
    ):
        by_week[week] = int(aggregation(value[1] for value in values))

    by_week_variation = {}
    for week, values in groupby(
        daily_variation.items(), key=lambda kvp: kvp[0].strftime("%Y S%W")
    ):
        by_week_variation[week] = sum(value[1] for value in values)
    return by_day, daily_variation, by_week, by_week_variation


def positivite():
    by_day = defaultdict(int)
    with open("sp-pos-quot-fra-2020-09-03-19h15.csv") as csvfile:
        reader = csv.DictReader(csvfile, dialect="datagouv")
        for row in reader:
            by_day[parse(row["jour"])] += int(row["P"])
    return analyze_data(by_day, aggregation=mean)


def donnees_hospitalieres_covid19(column="rea", aggregation=mean):
    by_day = defaultdict(int)
    csvs = list(Path(".").glob("donnees-hospitalieres-covid19-*.csv"))
    csvs.sort()
    csvname = csvs[-1]
    print("Using", csvname)
    with open(csvname) as csvfile:
        reader = csv.DictReader(csvfile, dialect="datagouv")
        for row in reader:
            if row["sexe"] != "0":  # specific
                continue
            by_day[parse(row["jour"])] += int(row[column])
    return analyze_data(by_day, aggregation=aggregation)


def donnees_hospitalieres_nouveau_covid19(column="incid_rea"):
    by_day = defaultdict(int)
    csvs = list(Path(".").glob("donnees-hospitalieres-nouveaux-covid19-*.csv"))
    csvs.sort()
    csvname = csvs[-1]
    print("Using", csvname)
    by_day = defaultdict(int)
    with open(csvname) as csvfile:
        reader = csv.DictReader(csvfile, dialect="datagouv")
        for row in reader:
            by_day[parse(row["jour"])] += int(row[column])
    return analyze_data(by_day, aggregation=sum)


def hospitalisations():
    print("# Hospitalisations")

    by_day, daily_var, by_week, weekly_var = donnees_hospitalieres_covid19("hosp")
    wiki_graph("Nombre d'hospitalisations", by_week.keys(), by_week.values())

    wiki_graph(
        "Variation du nombre d'hospitalisation", weekly_var.keys(), weekly_var.values()
    )

    by_day, daily_var, by_week, weekly_var = donnees_hospitalieres_nouveau_covid19(
        "incid_hosp"
    )
    wiki_graph("Nouvelles entrées en hopital", by_week.keys(), by_week.values())


def reanimation():
    print("# Reanimation")

    by_day, daily_var, by_week, weekly_var = donnees_hospitalieres_covid19("rea")
    wiki_graph("Nombre total en réa", by_week.keys(), by_week.values())
    wiki_graph(
        "Variation du nombre de cas en réa", weekly_var.keys(), weekly_var.values()
    )

    by_day, daily_var, by_week, weekly_var = donnees_hospitalieres_nouveau_covid19(
        "incid_rea"
    )
    wiki_graph("Nouvelles entrées en réanimation", by_week.keys(), by_week.values())


def retour_a_domicile():
    print("# Retours à domicile après hospitalisation")
    by_day, daily_var, by_week, weekly_var = donnees_hospitalieres_nouveau_covid19(
        "incid_rad"
    )
    wiki_graph(
        "Nombre cumulé de patients ayant été hospitalisés et de retour à domicile",
        by_week.keys(),
        by_week.values(),
    )


retour_a_domicile()

d = date(2020, 3, 17)
for _ in range(100):
    print(d, d.strftime("%Y S%W"))
    d += timedelta(days=1)
