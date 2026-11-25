"""Открытая адресация для целочисленных ключей. Число проб включает последнюю ячейку."""

from collections import Counter
from math import isqrt


_EMPTY = object()
_DELETED = object()


class HashTable:
    def __init__(self, size=65_521, method="linear", weak_hash=False):
        if size < 1 or method not in ("linear", "quadratic"):
            raise ValueError("Проверьте размер таблицы и метод пробирования")
        if method == "quadratic" and (
            size < 3 or size % 2 == 0
            or any(size % d == 0 for d in range(3, isqrt(size) + 1, 2))
        ):
            raise ValueError("Для квадратов требуется нечётный простой размер")
        self.size = size
        self.method = method
        self.weak_hash = weak_hash
        self.keys = [_EMPTY] * size
        self.values = [None] * size
        self.count = 0
        self.probes = 0
        self.displaced_inserts = 0

    def positions(self, key):
        home = (key % 10 if self.weak_hash else key) % self.size
        if self.method == "linear":
            for pos in range(home, self.size):
                yield pos
            yield from range(home)
        else:
            # i и m-i дают одинаковый квадрат по модулю простого m.
            for i in range((self.size + 1) // 2):
                yield (home + i * i) % self.size

    def _locate(self, key):
        """Возвращает (позиция, найден). Для вставки запоминает первую ячейку с меткой удаления."""
        first_deleted = None
        checked = 0
        for checked, pos in enumerate(self.positions(key), 1):
            stored = self.keys[pos]
            if stored is _EMPTY:
                self.probes += checked
                return (first_deleted if first_deleted is not None else pos), False
            if stored == key:
                self.probes += checked
                return pos, True
            if stored is _DELETED and first_deleted is None:
                first_deleted = pos
        self.probes += checked
        return first_deleted, False

    def insert(self, key, value):
        before = self.probes
        pos, found = self._locate(key)
        if pos is None:
            raise OverflowError("Свободной ячейки в последовательности проб нет")
        if not found:
            self.count += 1
            self.displaced_inserts += int(self.probes - before > 1)
        self.keys[pos] = key
        self.values[pos] = value

    def search(self, key, default=None):
        pos, found = self._locate(key)
        return self.values[pos] if found else default

    def delete(self, key):
        pos, found = self._locate(key)
        if not found:
            return False
        self.keys[pos] = _DELETED
        self.values[pos] = None
        self.count -= 1
        return True

    def cluster_lengths(self):
        """Число максимальных серий занятых ячеек каждой длины на кольце."""
        lengths = Counter()
        if self.count == self.size:
            return Counter({self.size: 1})
        start = next(i for i, k in enumerate(self.keys) if k is _EMPTY or k is _DELETED)
        run = 0
        for offset in range(1, self.size + 1):
            k = self.keys[(start + offset) % self.size]
            if k is _EMPTY or k is _DELETED:
                if run:
                    lengths[run] += 1
                    run = 0
            else:
                run += 1
        return lengths
