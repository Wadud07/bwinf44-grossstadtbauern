# Grossstadtbauern

**English summary:** A Python solver for task 5 "Großstadtbauern" of the
[44th Bundeswettbewerb Informatik](https://bwinf.de/bundeswettbewerb/) (German national computer science
competition), round 1, 2025. Three growing plants are planned over 12 months in 3-month cycles so that as many
three-ingredient dishes as possible can be cooked at least once a year. The solver combines a frequency heuristic, a
depth-first search for larger instances and a randomised local search with restarts; dishes are matched as
multisets. Pure Python standard library, no dependencies. The full documentation (German)
is in [`grossstadtbauern.pdf`](grossstadtbauern.pdf).

> Task and example inputs: © Bundeswettbewerb Informatik. Solution code and documentation: Mohammad Abdul Wadud.

---

Einfacher Solver zur Planung von 3 Anbauflächen über 12 Monate, um möglichst viele Gerichte mit 3 Zutaten anzubieten.

## 1. Funktionsweise des Programms: 
Das Programm liest eine Textdatei mit Zutaten und Gerichten (jedes Gericht besteht aus genau 3 Zutaten). Es ordnet jeder Anbaufläche eine Zutat für 3-Monats-Blöcke zu (zeitlich versetzte Starts) und versucht, die Anzahl der verschiedenen Gerichte zu maximieren, die in mindestens einem Monat vorkommen. Der Abgleich erfolgt mittels eines Multiset-Vergleichs (Reihenfolge irrelevant; Duplikate werden gezählt).

## 2. Format der Eingabedatei:
```
N
<Zutat 1>
...
<Zutat N>
M
<Zutat A1> <Zutat A2> <Zutat A3>
<Zutat B1> <Zutat B2> <Zutat B3>
...
```
Hinweise:
- Zutaten sind einzelne Token (Unterstriche werden automatisch in Leerzeichen umgewandelt).

- Jede Gerichtezeile muss genau 3 Einträge enthalten.

Beispiel snippet:
```
12
Kartoffel
Tomate
Zwiebel
...
12
Kartoffel Tomate Zwiebel
Kartoffel Kohl Karotte
...
```

## 3. Ausführen des Programms
Minimale Verwendung (verwendet die Standarddatei `eingabe/bauern.txt`, falls vorhanden):
```powershell
python loesung.py
``` 
Datendatei angeben:
```powershell
python loesung.py eingabe\bauern6.txt
```

Verhalten bei Beendigung:
- Kann die Datei nicht gelesen oder geparst werden: Das Programm gibt eine Fehlermeldung aus und beendet sich.

- Bei Erfolg: Plan, Abdeckung und Monatstabelle werden ausgegeben; Exit-Code 0.

## 4. Befehlszeilenargumente
Das Programm unterstützt derzeit ein einzelnes Positionsargument (den Pfad zur Eingabedatei). Es gibt noch keine optionalen Flags. Alles, was mit `--` beginnt, wird vom aktuellen Loader ignoriert.

Syntax:
```powershell
python loesung.py <path-to-input-file>
```

Beispiele:
```powershell
python loesung.py eingabe\bauern.txt      # Basisbeispiel verwenden
python loesung.py eingabe\bauern6.txt      # Größere Instanz

```

Wenn Sie den Pfad weglassen, versucht das Programm, `eingabe/bauern.txt` zu verwenden.

## 5. Ausgabeübersicht

Ausgegebene Abschnitte:
1. Zutatenliste und Häufigkeiten.

2. Ausgewählte Hauptzutaten (Häufigkeitsheuristik).

3. Zyklusplan (Startmonat jedes 3-Monats-Blocks pro Installation).

4. Monatsübersicht (die 3 Hauptzutaten + die Gerichte, die zu diesem Monat passen).

5. Zusammenfassung: Anzahl der abgedeckten Gerichte und deren Indizes.

Beispiel (gekürzt):
```
===== Anbauplan-Optimierung =====
Zutaten (...)
...
=== Ergebnis ===
Maximale Gerichte pro Jahr: 12 von 12
Abgedeckte Gerichte: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
```


## 6. Ordnerstruktur
```
loesung.py
eingabe/     # Eingabedateien (bauern*.txt)
README.md
grossstadtbauern.pdf  # Projektdokumentation (Lösungsidee, Umsetzung, Beispiele)
```


## 7. Anforderungen
Python 3.13 (nur Standardbibliothek). UTF-8-Textdateien.



