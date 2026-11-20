import sys
import os
import random
from collections import Counter

# ==============================================================================
#  Deklarierte Konstanten – Struktur- und algorithmische Parameter
# ==============================================================================

# Allgemeine Zeit-/Strukturparameter
MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
"""
- Liste der 12 Monate in deutscher Sprache
- Wird ausschließlich zur besseren Lesbarkeit bei der Ausgabeformatierung verwendet
- Druckzykluspläne und monatliche Flächenberichte
- Rasterdarstellung des Pflanzplans im Block __main__
"""

# Fallback-Datei, falls kein Pfad über argv übergeben wird
DEFAULT_INPUT_PATH = "eingabe/bauern.txt"  
"""
- Der Pfad ist relativ zum Arbeitsverzeichnis.
- Wird im __main__-Block zum Lesen von Eingabedaten verwendet, wenn kein Befehlszeilenargument angegeben ist.
- Sorgt für eine konsistente Standardeingabe in verschiedenen Ausführungen/Umgebungen.
- Der Name bauern.txt entspricht dem in der Projektbeschreibung dokumentierten Sonderfall.
"""

# Maximale Anzahl ausgewählter Zutaten nach Häufigkeit            
TOP_INGREDIENT_LIMIT = 12  
"""
- Begrenzt die Anzahl der wichtigsten Zutaten, die für die Bepflanzung berücksichtigt werden.
- Wenn ONLY_TOP_INGREDIENTS=True (Standard) ist, werden nur diese Zutaten bei der Planung verwendet.
"""  

# Festgelegter Änderungsplan (Kernrestriktion des Problems)
CHANGE_PATTERN = [1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2]
"""
- Definiert, welche Anlage ihre Zutaten jeden Monat ändert.
- Wird in plan_full_sequence und plan_best_sequence verwendet, um Pflanzbeschränkungen durchzusetzen.
- Die Länge beträgt 11 und deckt Übergänge von Monat 0 bis 11 (insgesamt 12 Monate) ab.
- CHANGE_PATTERN[t] = Index der Anlage (0, 1, 2), die sich von Monat t bis t+1 ändert.
- Beispiel: Von Monat 0 bis 1 ändert sich Anlage 1; von Monat 1 bis 2 ändert sich Anlage 2 usw.
"""

# zentrale Definition der Zyklus-Startmonate (Indices).
CYCLE_START_INDICES = {
    0: [0, 3, 6, 9],   # Anlage 0
    1: [1, 4, 7, 10],  # Anlage 1
    2: [2, 5, 8, 11],  # Anlage 2
}
"""
- Definiert gültige Startmonate für 3-monatige Bepflanzungszyklen für jede Anlage.
- Wird in assign_cycles, plan_full_sequence und plan_best_sequence verwendet, um Pflanzzuweisungen zu strukturieren.
- Stellt sicher, dass Zyklen nur in den angegebenen Monaten beginnen, um die Problemrestriktionen einzuhalten.
"""


# ====================================================================================
#  Globale Konfiguration – anpassbare Parameter für die gesamte Optimierungspipeline
# ====================================================================================

# Verhaltensschalter
ONLY_TOP_INGREDIENTS =  True
"""
- Um zu prüfen, ob nur die 12 wichtigsten Zutaten die besten Optimierungsergebnisse liefern oder ob die Nachbarsuche mit plan_best_sequence bessere Ergebnisse liefert.
- Bei „True“ werden nur die 12 häufigsten Zutaten bei Planung und Optimierung berücksichtigt.
- Bei „False“ werden alle Zutaten aus der Eingabe berücksichtigt.
"""
# Zufallsstartwert für Reproduzierbarkeit
RANDOM_SEED = 42
"""
- spezifizierter Startwert für den Zufallszahlengenerator, um konsistente Ergebnisse über verschiedene Ausführungen hinweg sicherzustellen
- Wird in Funktionen verwendet, die Zufälligkeit beinhalten: assign_cycles, plan_best_sequence, local_improve
- Ändern Sie diesen Wert, um unterschiedliche zufällige Variationen in der Ausgabe zu erhalten
"""
# Lokale Suchintensität
IMPROVE_ITERATIONS = 20000
"""
- Anzahl der Iterationen für die lokale Verbesserungsphase in der Funktion local_improve
- Größere Werte ermöglichen eine umfassendere Suche nach besseren Lösungen, erhöhen jedoch die Laufzeit
- Der Standardwert von 20000 ist ein Kompromiss zwischen Lösungsqualität und Leistung
    - Bei kleineren Eingaben läuft es schneller und liefert gute Ergebnisse
    - Bei größeren Eingaben wie bauern6.txt kann es länger dauern (5-6 Minuten +-), liefert jedoch bessere Ergebnisse
- Kann basierend auf der Eingabegröße und der gewünschten Optimierungstiefe angepasst werden
"""
# Anzahl der unabhängigen Neustarts der lokalen Verbesserungsheuristik
RANDOM_RESTARTS = 10
"""
- Jeder Neustart beginnt mit dem 'besten Gitter bisher' und führt 'IMPROVE_ITERATIONS' zufällige Bewegungen durch
- Mehr Neustarts erhöhen die Chancen, lokale Optima zu verlassen, erhöhen jedoch auch die Gesamtlaufzeit
- Der Standardwert von 10 bietet einen guten Kompromiss für die meisten Eingaben
"""


# ====================================================
#  Eingabetext lesen und parsen
# ====================================================

def lese_zutaten_tupel(source):
    """
    Liest Zutaten und Wunschgerichte aus einer Datei oder Liste von Zeilen und liefert:
        - die vollständige Zutatenliste
        - eine Liste von Tupeln (jeweils 3 Zutaten pro Gericht)
    """
    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = source
    lines = [l.strip() for l in lines if l.strip()]
    i = 0
    n = int(lines[i]); i += 1
    zutaten = [lines[i + j].replace("_", " ") for j in range(n)]
    i += n
    m = int(lines[i]); i += 1
    tupel = []
    for j in range(m):
        parts = [p.replace("_", " ") for p in lines[i + j].split() if p]
        if len(parts) != 3:
            raise ValueError(f"Ungültige Zeile: {lines[i + j]}")
        tupel.append(tuple(parts))
    return zutaten, tupel

# ====================================================
#  Zutaten haeufigkeit
# ====================================================

def zutaten_haeufigkeit(tupel_liste):
    """
    - Zählt die Häufigkeit jeder Zutat (durch einen collections.Counter) in der Liste der Wunschgerichte (Tupel-Liste).
    - Liefert den Counter zurück.
    """
    c = Counter()
    for t in tupel_liste:
        c.update(t)
    return c

# ====================================================
#  Top 12 zutaten
# ====================================================

def get_top_ingredients(haeufigkeit, max_12=12):
    """
    - Liefert die Liste der Top-12-Zutaten basierend auf der Häufigkeit.
    - Bei Gleichstand werden die Zutaten alphabetisch sortiert.
    """
    items = sorted(haeufigkeit.items(), key=lambda x: (-x[1], x[0]))
    return [i[0] for i in items[:max_12]]

# =========================================================================================================================
#  Bewertet ein Pflanzraster, um zu bestimmen, wie viele Schalen es abdeckt und welche konkreten Schalen abgedeckt sind.
# =========================================================================================================================

def compute_coverage(grid, dishes):
    """
    - Berechnet Anzahl einzigartiger abgedeckter Gerichte und IDs.
    - für jeden Monat wird der Zutaten-Counter der drei Anlagen gebildet.
    - Vergleicht diesen Counter mit jedem Gericht in der Liste.
    - benutzt collections.Counter für Multimengenvergleich.
    - Gibt die Gesamtanzahl abgedeckter Gerichte und deren Indizes zurück.
    """
    covered = set()
    for c in range(12):
        monthly_counter = Counter(grid[row][c] for row in range(3))
        for i, dish in enumerate(dishes):
            if Counter(dish) == monthly_counter:
                covered.add(i)
    return len(covered), list(covered)

# ========================================================================
#  Erstellt eine Liste aller Zyklus-Startpositionen für die drei Anlagen.
# ========================================================================

def get_cycles_list():
    """
    - Liefert eine Liste von (Anlage, Startmonat)-Tupeln für alle Zyklus-Startpositionen.
    - Nutzt die globale CYCLE_START_INDICES-Konstante.
    - wird von fast allen Planungs- und Verbesserungsfunktionen verwendet.
    """
    lst = []
    for r in range(3):
        for s in sorted(CYCLE_START_INDICES[r]):
            lst.append((r, s))
    return lst

# ====================================================
#  Setzt einen 3-Monats-Zyklus in das Pflanzraster.
# ====================================================

def set_cycle(grid, row, start, ingredient):
    """
    - Setzt die angegebene Zutat für einen 3-Monats-Zyklus in das Raster.
    - start, start+1, start+2 (mod 12) werden gesetzt.
    - wird überall dort verwendet, wo Zyklen zugewiesen werden müssen.
    """
    for k in range(3):
        grid[row][(start + k) % 12] = ingredient

# ====================================================
#  Erstellt ein leeres 3x12 Pflanzraster.
# ====================================================

def make_empty_grid():
    """
    - Erstellt ein leeres 3x12 Pflanzraster.
    - Wird in mehreren Funktionen verwendet, um neue Raster zu initialisieren.
    """
    return [[''] * 12 for _ in range(3)]

# =============================================================
#  Greedy Zuweisung von Zyklen basierend auf Zutatenhäufigkeit.
# =============================================================

def assign_cycles(values, dishes, haeufigkeit, only_top=True):
    """
    - Haupt-Greedy-Heuristic:
        - sortiert gerichte nach einem score basierend auf Zutatenhäufigkeit
        - versucht, jedes Gericht zuzuweisen, indem es verfügbare Zyklen füllt
        - füllt verbleibende Zyklen mit den häufigsten Zutaten
        - führt mehrere Durchläufe durch und behält das beste Raster bei
        - optional nur top-12-zutaten verwenden (only_top=True)
        - liefert das beste gefundene Raster zurück

    """
    random.seed(RANDOM_SEED)
    top_set = set(values) if only_top else set(haeufigkeit.keys())
    cycles = get_cycles_list()
    best_grid = make_empty_grid()
    best_cov, best_ids = 0, []
    
    for _ in range(5):
        grid = make_empty_grid()
        cycle_assign = [''] * len(cycles)
        used_dishes = set()

        dish_scores = []
        for idx, d in enumerate(dishes):
            score = sum(haeufigkeit.get(z, 0) for z in d)
            if only_top and all(z in top_set for z in d) and len(set(d)) == 3:
                score += 1000
            dish_scores.append((score, random.random(), d, idx))
        dish_scores.sort(reverse=True)

        for _, _, dish, idx in dish_scores:
            if idx in used_dishes:
                continue
            for month in range(12):
                active = [i for i, (r, s) in enumerate(cycles) if s <= month < s + 3]
                if len(active) != 3:
                    continue
                current = [cycle_assign[a] for a in active if cycle_assign[a]]
                if len(current) == 3 and Counter(current) == Counter(dish):
                    used_dishes.add(idx)
                    break
                needed = [ing for ing in dish if ing not in current]
                if len(needed) + len(current) != 3:
                    continue
                if only_top and any(ing not in top_set for ing in needed):
                    continue
                random.shuffle(needed)
                for ing in needed:
                    assigned = False
                    for a in active:
                        if not cycle_assign[a]:
                            cycle_assign[a] = ing
                            r, s = cycles[a]
                            set_cycle(grid, r, s, ing)
                            assigned = True
                            break
                    if not assigned:
                        break
                else:
                    used_dishes.add(idx)
                    break

        candidate_ings = sorted([x for x in values if x in top_set], key=lambda x: (haeufigkeit.get(x, 0), x), 
                                reverse=True) if only_top else sorted(haeufigkeit.keys(), key=lambda x: (haeufigkeit.get(x, 0), x), reverse=True)
        random.shuffle(candidate_ings)
        ing_count = Counter(ing for row in grid for ing in row if ing)
        for idx, (r, s) in enumerate(cycles):
            if not cycle_assign[idx]:
                best = None
                best_cov = -1
                for cand in candidate_ings:
                    if ing_count[cand] >= 2:
                        continue
                    temp_grid = [row[:] for row in grid]
                    set_cycle(temp_grid, r, s, cand)
                    cov, _ = compute_coverage(temp_grid, dishes)
                    if cov > best_cov:
                        best_cov = cov
                        best = cand
                if best:
                    cycle_assign[idx] = best
                    set_cycle(grid, r, s, best)
                    ing_count[best] += 3
                elif candidate_ings:
                    cycle_assign[idx] = candidate_ings[0]
                    set_cycle(grid, r, s, candidate_ings[0])
                    ing_count[cycle_assign[idx]] += 3

        cov, ids = compute_coverage(grid, dishes)
        uncovered_dishes = [(i, d) for i, d in enumerate(dishes) if i not in ids and (not only_top or all(z in top_set for z in d))]
        random.shuffle(uncovered_dishes)
        for idx, dish in uncovered_dishes[:10]:
            for month in range(12):
                active = [i for i, (r, s) in enumerate(cycles) if s <= month < s + 3 and not cycle_assign[i]]
                if len(active) >= len([i for i in dish if i not in [cycle_assign[a] for a in active if cycle_assign[a]]]):
                    needed = [i for i in dish if i not in [cycle_assign[a] for a in active if cycle_assign[a]]]
                    for ing in needed:
                        assigned = False
                        for a in active:
                            if not cycle_assign[a]:
                                cycle_assign[a] = ing
                                r, s = cycles[a]
                                set_cycle(grid, r, s, ing)
                                assigned = True
                                break
                        if not assigned:
                            break
                    else:
                        used_dishes.add(idx)
                        break

        cov, ids = compute_coverage(grid, dishes)
        if cov > best_cov or (cov == best_cov and len(ids) > len(best_ids)):
            best_grid = [row[:] for row in grid]
            best_cov, best_ids = cov, ids

    return best_grid


# ================================================================
#  Hilfsfunktion: Generiert alle Permutationen eines 3er-Tupels.
# ================================================================

def permutations_of(triple):
    """
    -Erzeugt alle 6 Permutationen eines 3er-Tupels.
    -wird nur beim start der exakten sequenz(Monat 0) verwendet.
    -jede permutation repräsentiert eine mögliche anordnung der zutaten auf die 3 anlagen.
    -liefert eine Liste von 6 Tupeln zurück.
    """
    a, b, c = list(triple)
    return [(a, b, c), (a, c, b), (b, a, c), (b, c, a), (c, a, b), (c, b, a)]


# =========================================================================================================
#  Erstellt eine strikte 12-Schalen-Sequenz, die dem festen Änderungsmuster folgt (nur kleine Eingaben).
# =========================================================================================================

def plan_full_sequence(dishes):
    """
    - für sehr kleine instanzen (<=12 Gerichte) wird per Tiefensuche (DFS) eine exact 12-Monats-Sequenz geplant 
      die folge von 12 Gerichten abdeckt die exact dem vorgegebenen 'CHANGE_PATTERN' folgen.
    - nachbarn: Gerichte, die sich in genau 2 Zutaten gemainsam haben
    - Jeder Übergang ersetzt exakt die Zutat der wechselnden Anlage.
    - Permutationen der drei Zutaten werden ausprobiert.
    - Sobald eine vollständige Sequenz gefunden ist, werden evtl. noch freie Zyklen mit Top-Zutaten aufgefüllt.
    - Rückgabe: (order, assignments, grid) oder ``None``.
    """
    n = len(dishes)
    if n == 0:
        return None
    dish_sets = [set(d) for d in dishes]
    neighbors = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(n):
            if i != j and len(dish_sets[i] & dish_sets[j]) == 2:
                neighbors[i].append(j)

    # =============================================================================================================
    #  Rekursive depth-first search (DFS) zur Planung der 12-step gerichte-sequenz folgend dem CHANGE_PATTERN.
    # =============================================================================================================

    def dfs(month, order, assignments, used, grid):
        """
        - Rekursive DFS zur Planung der 12-Monats-Sequenz.
        - month: aktueller Monat (0-11)
        - order: Liste der ausgewählten Gerichte-Indizes
        - assignments: Liste der Zutaten-Zuweisungen pro Monat
        - used: Menge der bereits verwendeten Gerichte-Indizes
        - grid: aktuelles Pflanzraster
        - nutzt nachbarschaftgraph (Gerichte mit 2 gemeinsamen Zutaten) und prüft gültige Übergänge gemäß CHANGE_PATTERN
        - bei erfolgreicher Planung wird (order, assignments, grid) zurückgegeben
        """
        if month == n or month == 12:
            return order, assignments, grid
        if month == 0:
            for dish_idx in range(n):
                if dish_idx in used:
                    continue
                used.add(dish_idx)
                for perm in permutations_of(dish_sets[dish_idx]):
                    new_grid = [row[:] for row in grid]
                    set_cycle(new_grid, 0, 0, perm[0])
                    set_cycle(new_grid, 0, 9, perm[0])
                    set_cycle(new_grid, 1, 1, perm[1])
                    set_cycle(new_grid, 1, 10, perm[1])
                    set_cycle(new_grid, 2, 2, perm[2])
                    set_cycle(new_grid, 2, 11, perm[2])
                    order.append(dish_idx)
                    assignments.append(perm)
                    res = dfs(month + 1, order, assignments, used, new_grid)
                    if res:
                        return res
                    order.pop()
                    assignments.pop()
                used.remove(dish_idx)
            return None

        change_inst = CHANGE_PATTERN[month - 1]
        prev_idx = order[-1]
        prev_set = dish_sets[prev_idx]
        prev_assign = assignments[-1]
        for cand in neighbors[prev_idx]:
            if cand in used:
                continue
            inter = dish_sets[cand] & prev_set
            if len(inter) != 2:
                continue
            removed = list(prev_set - inter)
            if len(removed) != 1:
                continue
            removed_ingr = removed[0]
            if prev_assign[change_inst] != removed_ingr:
                continue
            new_ingr = list(dish_sets[cand] - inter)[0]
            new_assign = list(prev_assign)
            new_assign[change_inst] = new_ingr
            if set(new_assign) != dish_sets[cand]:
                continue
            if month not in CYCLE_START_INDICES[change_inst]:
                continue
            new_grid = [row[:] for row in grid]
            set_cycle(new_grid, change_inst, month, new_ingr)
            used.add(cand)
            order.append(cand)
            assignments.append(tuple(new_assign))
            res = dfs(month + 1, order, assignments, used, new_grid)
            if res:
                return res
            order.pop()
            assignments.pop()
            used.remove(cand)
        return None

    sys.setrecursionlimit(5000)
    for start in range(n):
        result = dfs(0, [], [], set(), [[''] * 12 for _ in range(3)])
        if result:
            order, assignments, grid = result
            if len(order) < 12:
                haeufigkeit = zutaten_haeufigkeit(dishes)
                top_ingredients = get_top_ingredients(haeufigkeit, TOP_INGREDIENT_LIMIT)
                for r in range(3):
                    for start in CYCLE_START_INDICES[r]:
                        if not grid[r][start]:
                            ingredient = top_ingredients[start % len(top_ingredients)]
                            set_cycle(grid, r, start, ingredient)
            return order, assignments, grid
    return None

# ==================================================================================================
#  Tiefensuche mit entspannten Nachbarbeschränkungen – zielt auf ~10–12 abgedeckte Gerichte ab.
# ==================================================================================================

def plan_best_sequence(dishes, limit=12, max_states=20000000, only_top=True):
    """
    Erweiterte DFS-Heuristik für größere Instanzen.
    - Nachbarschaft: mindestens 1 gemeinsame Zutat.
    - Startgerichte werden nach einem kombinierten Score
      (Häufigkeit + Nachbarschaftsgrad) ausgewählt.
    - Während der Suche wird laufend die aktuelle Coverage geprüft;
      das beste Zwischenergebnis (inkl. gefüllter Restzyklen) wird
      gespeichert.
    - Frühes Abbruchkriterium: genug Gerichte abgedeckt oder
      'limit' erreicht.
    - Optional nur Top-Zutaten.
    - liefert: (order, assignments, best_grid).
    """
    random.seed(RANDOM_SEED)
    n = len(dishes)
    if n == 0:
        return None
    dish_sets = [set(d) for d in dishes]
    neighbors = {i: [] for i in range(n)}
    neighbor_threshold = 1
    for i in range(n):
        for j in range(n):
            if i != j and len(dish_sets[i] & dish_sets[j]) >= neighbor_threshold:
                neighbors[i].append(j)
    haeufigkeit = zutaten_haeufigkeit(dishes)
    dish_scores = [(sum(haeufigkeit.get(z, 0) for z in d), len(neighbors[i]), random.random(), d, i) for i, d in enumerate(dish_sets)]
    dish_order = [i for _, _, _, _, i in sorted(dish_scores, key=lambda x: (x[0], x[1], x[2]), reverse=True)]
    for i in range(n):
        neighbors[i].sort(key=lambda x: (sum(haeufigkeit.get(z, 0) for z in dish_sets[x]), len(neighbors[x]), random.random()), reverse=True)


    # ================================================================
    #  Hilfsfunktion: Bewertet die Coverage eines Rasters.
    # ================================================================

    def compute_coverage_score(grid):
        """
        -wrapper um compute_coverage, wird in der DFS verwendet
        -liefert die Anzahl abgedeckter Gerichte und deren IDs zurück
        -dient der Bewertung aktueller und bester Raster während der Suche
        """
        cov, ids = compute_coverage(grid, dishes)
        return cov, ids

    # ========================================================================
    #  Hilfsfunktion: Greedily Füllt leere Zyklen mit hochfrequenten Zutaten.
    # ========================================================================

    def fill_remaining_cycles(grid, used_ingredients, allowed_ingredients, haeufigkeit):
        """
        -Nachdem die DFS eine Teilsequenz gebaut hat, werden alle noch freien Zyklen mit den häufigsten erlaubten Zutaten gefüllt.
        -Für jeden freien Zyklus wird die Zutat gewählt, die die Coverage maximiert.
        -Falls keine Verbesserung möglich ist, wird die häufigste Zutat genommen.
        -liefert das gefüllte Raster zurück.
        """
        temp_grid = [row[:] for row in grid]
        cycles = get_cycles_list()
        candidate_ingredients = sorted([i for i in allowed_ingredients if i not in used_ingredients or 
                                        sum(row.count(i) for row in grid) < 3], key=lambda x: (haeufigkeit.get(x, 0), x), reverse=True)
        for r in range(3):
            for start in CYCLE_START_INDICES[r]:
                if not temp_grid[r][start]:
                    best_ing = None
                    best_cov = 0
                    for cand in candidate_ingredients:
                        test_grid = [row[:] for row in temp_grid]
                        set_cycle(test_grid, r, start, cand)
                        cov, _ = compute_coverage(test_grid, dishes)
                        if cov > best_cov:
                            best_cov = cov
                            best_ing = cand
                    if best_ing:
                        set_cycle(temp_grid, r, start, best_ing)
                        if best_ing in candidate_ingredients:
                            candidate_ingredients.remove(best_ing)
        return temp_grid

    best_order = []
    best_assignments = []
    best_grid = [[''] * 12 for _ in range(3)]
    best_coverage = 0
    top_ingredients = get_top_ingredients(haeufigkeit, TOP_INGREDIENT_LIMIT)
    allowed_ingredients = top_ingredients if only_top else list(haeufigkeit.keys())

    # =============================================================================================================
    #  Rekursives DFS mit gelockerten Einschränkungen und frühzeitiger Aktualisierung der besten Lösung.
    # =============================================================================================================

    def dfs(month, order, assignments, used, grid, start_dish=None):
        """
        -Haupt-DFS der plan_best_sequence.
        - Erlaubt Nachbarn mit ≥1 gemeinsamer Zutat 
        - Prüft laufend die aktuelle Coverage und speichert das beste Grid
        - Füllt bei vielversprechenden Teillös unclean Zyklen mit fill_remaining_cycles
        - Bricht früh ab, wenn Ziel-Coverage erreicht ist
        - Begrenzt Zustände mit 'max_states' pro Monat

        """
        nonlocal best_order, best_assignments, best_grid, best_coverage
        current_coverage, current_ids = compute_coverage_score(grid)
        used_ingredients = set(ing for row in grid for ing in row if ing)
        score = current_coverage * 100000 + len(current_ids) * 1000
        best_ids = compute_coverage_score(best_grid)[1]
        best_score = best_coverage * 100000 + len(best_ids) * 1000
        if score > best_score:
            temp_grid = fill_remaining_cycles(grid, used_ingredients, allowed_ingredients, haeufigkeit)
            temp_coverage, temp_ids = compute_coverage_score(temp_grid)
            temp_score = temp_coverage * 100000 + len(temp_ids) * 1000
            if temp_score > best_score:
                best_order = order[:]
                best_assignments = assignments[:]
                best_grid = [row[:] for row in temp_grid]
                best_coverage = temp_coverage
                if temp_coverage >= len(dishes) // 10:
                    return True
        if month >= limit:
            return False

        state_count = 0  # Move state_count inside dfs
        if month == 0:
            if start_dish is None:
                return False
            if start_dish in used:
                return False
            used.add(start_dish)
            for perm in permutations_of(dish_sets[start_dish]):
                new_grid = [row[:] for row in grid]
                set_cycle(new_grid, 0, 0, perm[0])
                set_cycle(new_grid, 0, 9, perm[0])
                set_cycle(new_grid, 1, 1, perm[1])
                set_cycle(new_grid, 1, 10, perm[1])
                set_cycle(new_grid, 2, 2, perm[2])
                set_cycle(new_grid, 2, 11, perm[2])
                order.append(start_dish)
                assignments.append(perm)
                if dfs(month + 1, order, assignments, used, new_grid):
                    return True
                order.pop()
                assignments.pop()
            used.remove(start_dish)
            return False

        change_inst = CHANGE_PATTERN[month - 1]
        cycle_month = month
        for start in CYCLE_START_INDICES[change_inst]:
            if start <= month:
                cycle_month = start
            else:
                break

        candidates = neighbors[order[-1]]
        for cand in candidates[:50]:
            if cand in used:
                continue
            inter = dish_sets[cand] & dish_sets[order[-1]]
            if len(inter) < neighbor_threshold:
                continue
            removed = list(dish_sets[order[-1]] - inter)
            if len(removed) > 2:
                continue
            removed_ingr = removed[0]
            if assignments[-1][change_inst] != removed_ingr:
                continue
            new_ingr = list(dish_sets[cand] - inter)[0]
            new_assign = list(assignments[-1])
            new_assign[change_inst] = new_ingr
            if set(new_assign) != dish_sets[cand] or month not in CYCLE_START_INDICES[change_inst]:
                continue
            new_grid = [row[:] for row in grid]
            set_cycle(new_grid, change_inst, month, new_ingr)
            used.add(cand)
            order.append(cand)
            assignments.append(tuple(new_assign))
            state_count += 1
            if dfs(month + 1, order, assignments, used, new_grid):
                return True
            order.pop()
            assignments.pop()
            used.remove(cand)
            if state_count >= max_states:
                break
        return False

    for start in dish_order[:5]:
        if dfs(0, [], [], set(), [[''] * 12 for _ in range(3)], start_dish=start):
            break

    if best_order:
        best_grid = fill_remaining_cycles(best_grid, set(ing for row in best_grid for ing in row if ing), allowed_ingredients, haeufigkeit)
    return best_order, best_assignments, best_grid

# ========================================================================================================================
#  Zufällige lokale Suche (Austauschen/Ersetzen/Zielen auf nicht abgedeckte Gerichte) zur Verbesserung eines Rasters.
# ========================================================================================================================

def local_improve(grid, dishes, allowed_ingredients, haeufigkeit, iterations=IMPROVE_ITERATIONS, restarts=RANDOM_RESTARTS, only_top=True):
    """
    Lokale Verbesserungsheuristik.
    - Tausch zweier belegter Zyklen (40 % Wahrscheinlichkeit).
    - Ersetzen eines Zyklus durch eine andere erlaubte Zutat (40 %).
    - Zielgerichtetes Wechseln zu einem noch nicht abgedeckten Gericht (20 %).
    - Akzeptanz mit geringer Wahrscheinlichkeit auch bei gleicher Abdeckung
      (Random Hill Climbing).
    - Mehrere Neustarts, viele Iterationen.
    - Abschließend ein deterministischer Durchlauf zur gezielten Abdeckung zusätzlicher Gerichte.
    - Rückgabe: (verbessertes Raster, Abdeckung, Liste der abgedeckten Indizes)
    """
    random.seed(RANDOM_SEED)
    top_set = set(allowed_ingredients) if only_top else set(haeufigkeit.keys())
    best_grid = [row[:] for row in grid]
    best_cov, best_ids = compute_coverage(best_grid, dishes)
    cycles = [
        (0, 0), (0, 3), (0, 6), (0, 9),
        (1, 1), (1, 4), (1, 7), (1, 10),
        (2, 2), (2, 5), (2, 8), (2, 11)
    ]
    allowed = allowed_ingredients if only_top else list(haeufigkeit.keys())
    uncovered_dishes = [(i, d) for i, d in enumerate(dishes) if i not in best_ids and (not only_top or all(z in top_set for z in d))]

    for _ in range(restarts):
        current = [row[:] for row in best_grid]
        current_cov, current_ids = compute_coverage(current, dishes)
        for _ in range(iterations):
            move_type = random.random()
            if move_type < 0.4:  # Swap cycles
                i, j = random.sample(range(len(cycles)), 2)
                r1, s1 = cycles[i]
                r2, s2 = cycles[j]
                a = current[r1][s1]
                b = current[r2][s2]
                if a == b or not a or not b:
                    continue
                new_grid = [row[:] for row in current]
                set_cycle(new_grid, r1, s1, b)
                set_cycle(new_grid, r2, s2, a)
                cov, ids = compute_coverage(new_grid, dishes)
                if cov > current_cov or (cov == current_cov and (len(ids) > len(current_ids) or random.random() < 0.1)):
                    current = new_grid
                    current_cov, current_ids = cov, ids
                    if cov > best_cov or (cov == best_cov and len(ids) > len(best_ids)):
                        best_grid = [row[:] for row in new_grid]
                        best_cov, best_ids = cov, ids
                        uncovered_dishes = [(i, d) for i, d in enumerate(dishes) if i not in best_ids and (not only_top or all(z in top_set for z in d))]
            elif move_type < 0.8:  # Replace with allowed ingredient
                i = random.randrange(len(cycles))
                r, s = cycles[i]
                curr_ing = current[r][s]
                candidate_list = [x for x in allowed if x != curr_ing]
                if not candidate_list:
                    continue
                cand = random.choice(candidate_list)
                if only_top and cand not in top_set:
                    continue
                new_grid = [row[:] for row in current]
                set_cycle(new_grid, r, s, cand)
                cov, ids = compute_coverage(new_grid, dishes)
                if cov > current_cov or (cov == current_cov and (len(ids) > len(current_ids) or random.random() < 0.1)):
                    current = new_grid
                    current_cov, current_ids = cov, ids
                    if cov > best_cov or (cov == best_cov and len(ids) > len(best_ids)):
                        best_grid = [row[:] for row in new_grid]
                        best_cov, best_ids = cov, ids
                        uncovered_dishes = [(i, d) for i, d in enumerate(dishes) if i not in best_ids and (not only_top or all(z in top_set for z in d))]
            else:  # Target uncovered dish
                if not uncovered_dishes:
                    continue
                i = random.randrange(len(cycles))
                r, s = cycles[i]
                _, dish = random.choice(uncovered_dishes)
                cand = random.choice(list(dish))
                if only_top and cand not in top_set:
                    continue
                new_grid = [row[:] for row in current]
                set_cycle(new_grid, r, s, cand)
                cov, ids = compute_coverage(new_grid, dishes)
                if cov > current_cov or (cov == current_cov and (len(ids) > len(current_ids) or random.random() < 0.1)):
                    current = new_grid
                    current_cov, current_ids = cov, ids
                    if cov > best_cov or (cov == best_cov and len(ids) > len(best_ids)):
                        best_grid = [row[:] for row in new_grid]
                        best_cov, best_ids = cov, ids
                        uncovered_dishes = [(i, d) for i, d in enumerate(dishes) if i not in best_ids and (not only_top or all(z in top_set for z in d))]

    # Final pass: try to cover additional dishes
    for idx, dish in uncovered_dishes[:10]:
        for month in range(12):
            active = [i for i, (r, s) in enumerate(cycles) if s <= month < s + 3]
            if len(active) != 3:
                continue
            current = [best_grid[r][s] for i, (r, s) in enumerate(cycles) if i in active]
            needed = [ing for ing in dish if ing not in current]
            if len(needed) + len([i for i in current if i]) != 3:
                continue
            if only_top and any(ing not in top_set for ing in needed):
                continue
            temp_grid = [row[:] for row in best_grid]
            for ing in needed:
                assigned = False
                for i in active:
                    r, s = cycles[i]
                    if not temp_grid[r][s]:
                        set_cycle(temp_grid, r, s, ing)
                        assigned = True
                        break
                if not assigned:
                    break
            else:
                cov, ids = compute_coverage(temp_grid, dishes)
                if cov > best_cov or (cov == best_cov and len(ids) > len(best_ids)):
                    best_grid = [row[:] for row in temp_grid]
                    best_cov, best_ids = cov, ids

    return best_grid, best_cov, best_ids

# ====================================================
#  Druckt einen kompakten, zyklusbasierten Pflanzplan.
# ====================================================

def print_cycle_plan(grid, months):
    """
    - Druckt Zyklen-basierten Anbauplan.
    - Zeigt für jede Anlage die Startmonate und die zugewiesene Zutat.
    - gut lesbar für den Benutzer.

    """
    print("\nAnbauplan (nach Zyklen):")
    print("Anlage\tStartmonat\tZutat")
    print("-" * 30)
    starts = [
        ('1', months[0], 0, 0), ('1', months[3], 3, 0), ('1', months[6], 6, 0), ('1', months[9], 9, 0),
        ('2', months[1], 1, 1), ('2', months[4], 4, 1), ('2', months[7], 7, 1), ('2', months[10], 10, 1),
        ('3', months[2], 2, 2), ('3', months[5], 5, 2), ('3', months[8], 8, 2), ('3', months[11], 11, 2)
    ]
    for anlage, start, s_idx, row in starts:
        zutat = grid[row][s_idx]
        print(f"{anlage}\t{start:<10}\t{zutat}")

# ====================================================
#  Monatstabelle: Zutaten pro Monat + Liste der dazu passenden Gerichte.
# ====================================================

def print_monthly_coverage(grid, dishes, months):
    """
    - Druckt monatliche Tabelle mit Verfügbarkeit und Matches.
    - Für jeden Monat werden die drei Zutaten (eine pro Anlage) sowie
      alle Gerichte, deren Zutaten-Multiset exakt übereinstimmen,
    - angezeigt (Nummern 1-basiert).  Nutzt 'Counter' für Multiset-Vergleich.
    """
    print("\nMonatliche Verfügbarkeit und passende Gerichte:")
    # Header
    col_w = 12
    header = "Monat".ljust(col_w) + " " + "Zutat 1".ljust(8) + " " + "Zutat 2".ljust(8) + " " + "Zutat 3".ljust(8) + " " + "Passende Gerichte"
    print(header)
    print("-" * len(header))
    for c, monat in enumerate(months):
        items = [grid[r][c] for r in range(3)]
        # Show exact items (in cycle order)
        matching = [i+1 for i, dish in enumerate(dishes) if Counter(dish) == Counter(items)]
        matches_str = (', '.join(map(str, matching)) if matching else 'Keine')
        print(f"{monat:<{col_w}} {items[0]:<8} {items[1]:<8} {items[2]:<8} {matches_str}")


# =======================================================================================================
#  Programmeinstiegspunkt – liest Eingaben, wählt Algorithmus aus, verbessert, druckt Ergebnisse.
# =======================================================================================================

if __name__ == "__main__":
    """
    - hauptprogramm
    - liest eingabe von datei oder stdin
    - berechnet zutatenhäufigkeit und wählt top-12-zutaten aus
    - für kleine instanzen (<=12 gerichte) wird plan_full_sequence verwendet
    - für größere instanzen wird plan_best_sequence oder assign_cycles + local_improve verwendet
    - druckt anbauplan, abgedeckte gerichte und monatliche übersicht
    - nutzbare eingabeformate: dateipfad als argument, stdin, standarddatei, beispiel
    - gibt aus:
        - anbauplan
        - monatliche verfügbarkeit und passende gerichte
        - grid-übersicht
        - coverage statistik
        - endergebnisse
    """
    dateipfad = DEFAULT_INPUT_PATH
    zutaten, tupel_liste = None, None

    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        try:
            zutaten, tupel_liste = lese_zutaten_tupel(sys.argv[1])
            dateipfad = sys.argv[1]
            print(f"Eingabe gelesen aus: {dateipfad}")
        except Exception as e:
            print(f"Fehler beim Lesen von '{sys.argv[1]}': {e}")
    if zutaten is None:
        if os.path.exists(dateipfad):
            try:
                zutaten, tupel_liste = lese_zutaten_tupel(dateipfad)
                print(f"Eingabe gelesen aus: {dateipfad}")
            except Exception as e:
                print(f"Fehler beim Lesen von '{dateipfad}': {e}")
                print("Verwende stdin oder Beispiel-Eingabe.")
                try:
                    lines = sys.stdin.readlines()
                    if lines:
                        zutaten, tupel_liste = lese_zutaten_tupel(lines)
                        print("Eingabe von stdin gelesen.")
                except Exception as e:
                    print(f"Fehler bei stdin: {e}. Verwende Beispiel-Eingabe.")
        else:
            print(f"Standarddatei '{dateipfad}' nicht gefunden. Verwende stdin oder Beispiel-Eingabe.")

    if zutaten is None or tupel_liste is None:
        raise RuntimeError("Konnte Eingabe nicht laden. Programm abgebrochen.")

    haeufigkeit = zutaten_haeufigkeit(tupel_liste)
    anbau_liste = get_top_ingredients(haeufigkeit, max_12=TOP_INGREDIENT_LIMIT)
    months = MONTHS

    print("===== Anbauplan-Optimierung =====\n")
    print(f"Zutaten (insgesamt {len(zutaten)}): {zutaten}")
    print(f"\nWunschgerichte (insgesamt {len(tupel_liste)}):")
    for i, t in enumerate(tupel_liste, 1):
        print(f"  Gericht {i}: {' '.join(t)}")
    print("\nHäufigkeit der Zutaten:")
    for z, anz in haeufigkeit.most_common():
        print(f"  {z}: {anz}")
    print(f"\nAusgewählte Zutaten für Anbau (top {min(TOP_INGREDIENT_LIMIT, len(zutaten))} nach Häufigkeit): {anbau_liste}")

    sequence_result = None
    if len(tupel_liste) <= TOP_INGREDIENT_LIMIT:
        sequence_result = plan_full_sequence(tupel_liste)
    if sequence_result:
        order, assignments, grid = sequence_result
        print(f"len(tupel_liste): {len(order)}, TOP_INGREDIENT_LIMIT: {TOP_INGREDIENT_LIMIT}")
    else:
        grid_dfs = None
        if not ONLY_TOP_INGREDIENTS:
            seq_result = plan_best_sequence(tupel_liste, limit=TOP_INGREDIENT_LIMIT, only_top=False)
            if seq_result:
                order, assignments, grid_dfs = seq_result
                print(f"len(tupel_liste): {len(order)}, TOP_INGREDIENT_LIMIT: {TOP_INGREDIENT_LIMIT} (using plan_best_sequence)")
        grid_greedy = assign_cycles(anbau_liste, tupel_liste, haeufigkeit, only_top=ONLY_TOP_INGREDIENTS)
        print(f"len(tupel_liste): 0, TOP_INGREDIENT_LIMIT: {TOP_INGREDIENT_LIMIT} (using assign_cycles)")

        grid_greedy, cov_greedy, ids_greedy = local_improve(grid_greedy, tupel_liste, anbau_liste, haeufigkeit, only_top=ONLY_TOP_INGREDIENTS)
        if grid_dfs:
            grid_dfs, cov_dfs, ids_dfs = local_improve(grid_dfs, tupel_liste, anbau_liste, haeufigkeit, only_top=False)
            if cov_dfs > cov_greedy or (cov_dfs == cov_greedy and len(ids_dfs) > len(ids_greedy)):
                grid = grid_dfs
                print(f"Selected DFS grid with coverage: {cov_dfs}")
            else:
                grid = grid_greedy
                print(f"Selected greedy grid with coverage: {cov_greedy}")
        else:
            grid = grid_greedy
            print(f"Selected greedy grid with coverage: {cov_greedy}")

    print_cycle_plan(grid, months)
    num_covered, covered_ids = compute_coverage(grid, tupel_liste)
    print(f"\n=== Ergebnis ===")
    print(f"Maximale Gerichte pro Jahr: {num_covered} von {len(tupel_liste)}")
    if covered_ids:
        print(f"Abgedeckte Gerichte: {sorted([idx + 1 for idx in covered_ids])}")
    else:
        print("Keine Gerichte abgedeckt.")
    print_monthly_coverage(grid, tupel_liste, months)
    print("\nMonatliche Verteilung (Grid-Übersicht):")
    print("Monat:   " + " ".join([m[:3] for m in months]))
    for r, row in enumerate(grid):
        print(f"Anlage {r+1}: " + "  ".join([cell[:3] if len(cell)>3 else cell.ljust(3) for cell in row]))
    print("=== Ende ===")