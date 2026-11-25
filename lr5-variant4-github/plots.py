"""Графики по сохранённым протоколам. Самостоятельный запуск: python plots.py."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METHODS = {"linear": ("Линейное", "#275885", "o"),
           "quadratic": ("Квадратичное", "#128575", "s")}


def read(root, name):
    with (root / "results" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style(ax):
    ax.grid(axis="y", color="#dce3e8", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)


def draw(root):
    folder = root / "figures"
    folder.mkdir(exist_ok=True)
    loads = read(root, "load.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), layout="constrained")
    for ax, col, title in zip(axes, ("hit_probes", "miss_probes"),
                              ("Успешный поиск", "Неуспешный поиск")):
        for method, (label, color, marker) in METHODS.items():
            rows = [r for r in loads if r["method"] == method]
            ax.plot([float(r["alpha"]) for r in rows], [float(r[col]) for r in rows],
                    marker=marker, color=color, label=label, linewidth=2)
        if col == "miss_probes":
            alpha = [0.10 + i * 0.001 for i in range(851)]
            ax.plot(alpha, [1 / (1 - a) for a in alpha], "--", color="#994c23",
                    linewidth=1.7, label="Оценка 1/(1−α)")
            ax.set_yscale("log")
            ax.set_yticks([1, 2, 5, 10, 20, 50, 100, 200], labels=["1","2","5","10","20","50","100","200"])
        ax.set_xticks([.1, .3, .5, .7, .9, .95], labels=["0,1","0,3","0,5","0,7","0,9","0,95"])
        ax.tick_params(axis="x", labelrotation=24)
        ax.set_xlabel("Коэффициент заполнения α")
        ax.set_ylabel("Среднее число проб на запрос")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.legend(loc="upper left", frameon=False, fontsize=8.5)
        style(ax)
    fig.savefig(folder / "load_probes.png", dpi=175)
    plt.close(fig)

    data = read(root, "clusters.csv")
    groups = [(1,1),(2,3),(4,7),(8,15),(16,31),(32,63),(64,10**9)]
    labels = ["1","2–3","4–7","8–15","16–31","32–63","64+"]
    fig, ax = plt.subplots(figsize=(8.4, 3.65), layout="constrained")
    for j, (method, (label, color, _)) in enumerate(METHODS.items()):
        rows = [r for r in data if r["method"] == method]
        counts = [sum(int(r["clusters"]) for r in rows if lo <= int(r["length"]) <= hi)
                  for lo, hi in groups]
        ax.bar([i + (j - .5) * .37 for i in range(len(groups))], counts,
               width=.36, label=label, color=color)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel("Длина непрерывного занятого участка, ячеек")
    ax.set_ylabel("Количество участков")
    ax.legend(frameon=False)
    style(ax)
    fig.savefig(folder / "clusters.png", dpi=175)
    plt.close(fig)


if __name__ == "__main__":
    draw(Path(__file__).resolve().parent)
