"""Лабораторная работа № 5. Булова Екатерина, БИ 2-1, вариант 4."""

import argparse
import csv
import json
import platform
import random
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from hash_table import HashTable

ROOT = Path(__file__).resolve().parent
M, BASE_N, QUERIES, REPEATS, SEED = 65_521, 40_000, 4_000, 3, 4
LOADS = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95)
METHODS = ("linear", "quadratic")


def save_csv(name, rows):
    with (ROOT / "results" / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def time_queries(lookup, queries):
    start = perf_counter_ns()
    for key in queries:
        lookup(key)
    return (perf_counter_ns() - start) / 1_000_000


def measure(method, keys, hits, misses):
    insert_times, hit_times, miss_times = [], [], []
    for _ in range(REPEATS):
        builtin = method == "dict"
        table = {} if builtin else HashTable(M, method)
        insert = table.__setitem__ if builtin else table.insert
        lookup = table.get if builtin else table.search
        start = perf_counter_ns()
        for key in keys:
            insert(key, key)
        insert_times.append((perf_counter_ns() - start) / 1_000_000)
        after_insert = 0 if builtin else table.probes
        hit_times.append(time_queries(lookup, hits))
        after_hits = 0 if builtin else table.probes
        miss_times.append(time_queries(lookup, misses))
        after_misses = 0 if builtin else table.probes
    assert (len(table) if builtin else table.count) == len(keys)
    assert all(lookup(k) == k for k in hits) and all(lookup(k) is None for k in misses)
    row = dict(method=method, n=len(keys), m="" if builtin else M,
               alpha="" if builtin else len(keys) / M,
               insert_ms=median(insert_times), hit_ms=median(hit_times),
               miss_ms=median(miss_times),
               insert_probes="" if builtin else after_insert / len(keys),
               hit_probes="" if builtin else (after_hits - after_insert) / len(hits),
               miss_probes="" if builtin else (after_misses - after_hits) / len(misses))
    return row, table


def hash_comparison(keys, hits, misses):
    """Одинаковая полная выборка для обеих функций; отдельный запуск без таймера."""
    rows = []
    for weak in (False, True):
        addresses = {k % (10 if weak else M) for k in keys}
        for method in METHODS:
            table = HashTable(M, method, weak_hash=weak)
            for key in keys:
                table.insert(key, key)
            assert table.count == len(keys)
            insert_probes = table.probes
            for key in hits:
                value = table.search(key)
                if value != key:
                    raise AssertionError("Потерян вставленный ключ")
            after_hits = table.probes
            for key in misses:
                value = table.search(key)
                if value is not None:
                    raise AssertionError("Найден отсутствующий ключ")
            rows.append(dict(method=method, hash="mod10" if weak else "mod_m",
                             n=len(keys), occupied_homes=len(addresses),
                             repeated_homes=len(keys) - len(addresses),
                             displaced_inserts=table.displaced_inserts,
                             extra_insert_probes=insert_probes - len(keys),
                             insert_probes=insert_probes / len(keys),
                             hit_probes=(after_hits - insert_probes) / len(hits),
                             miss_probes=(table.probes - after_hits) / len(misses)))
    return rows


def check():
    for method in METHODS:
        table = HashTable(7, method)
        keys = [5, 12, 19]
        for k in keys:
            table.insert(k, k)
        assert table.count == 3 and table.delete(5)
        assert table.search(19) == 19
        table.insert(19, -1)  # Обновление существующего ключа за удалённой ячейкой.
        assert table.count == 2 and table.search(19) == -1
        table.insert(26, 0)
        assert table.keys[5] == 26 and table.probes > 0
        assert table.search(26) == 0 and not table.delete(33)
    limited = HashTable(7, "quadratic")
    for k in (0, 7, 14, 21):
        limited.insert(k, k)
    try:
        limited.insert(28, 28)
    except OverflowError:
        assert limited.count == 4 and limited.search(28) is None
    else:
        raise AssertionError("Не обнаружено исчерпание квадратов")
    wrap = HashTable(7)
    for k in (5, 6, 0):
        wrap.insert(k, k)
    assert wrap.cluster_lengths() == {3: 1}


def run():
    (ROOT / "results").mkdir(exist_ok=True)
    maximum = round(M * max(LOADS))
    sample = random.Random(SEED).sample(range(1, 2**31), maximum + QUERIES)
    keys, misses = sample[:maximum], sample[maximum:]

    def hits_for(n):
        return random.Random(SEED + n).sample(keys[:n], QUERIES)

    main_hits = hits_for(BASE_N)
    baseline, clusters = [], []
    for method in (*METHODS, "dict"):
        row, table = measure(method, keys[:BASE_N], main_hits, misses)
        baseline.append(row)
        if method in METHODS:
            lengths = table.cluster_lengths()
            assert sum(length * count for length, count in lengths.items()) == BASE_N
            clusters.extend(dict(method=method, length=length, clusters=count)
                            for length, count in sorted(lengths.items()))
    save_csv("baseline.csv", baseline)
    save_csv("clusters.csv", clusters)
    sweep = []
    for target in LOADS:
        n = round(M * target)
        hits = hits_for(n)
        for method in METHODS:
            row, _ = measure(method, keys[:n], hits, misses)
            row.update(target_alpha=target, uniform_miss=1 / (1 - n / M))
            sweep.append(row)
    save_csv("load.csv", sweep)
    print("В4 рассчитано. Сравниваются хеш-функции на 40 000 ключей…", flush=True)
    comparison_queries = 256
    hashes = hash_comparison(keys[:BASE_N], main_hits[:comparison_queries],
                             misses[:comparison_queries])
    save_csv("hashes.csv", hashes)
    meta = dict(python=platform.python_version(), system=platform.system(), m=M,
                n=BASE_N, seed=SEED, queries=QUERIES, repeats=REPEATS,
                comparison_queries=comparison_queries)
    (ROOT / "results" / "run.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    from plots import draw
    draw(ROOT)
    print("Результаты записаны в results/, графики — в figures/.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="только проверить таблицы")
    args = parser.parse_args()
    check()
    if args.check:
        print("Проверки хеш-таблиц пройдены.")
    else:
        run()
