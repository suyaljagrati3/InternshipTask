import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Data ───────
days        = ["Day -1", "Day 0", "Day -2"]
osm_pnl     = [1035,     1108,    471]
pep_pnl     = [34685,    34760,   34822]
total_pnl   = [35720,    35868,   35293]
osm_trades  = [85,       97,      54]
pep_trades  = [7,        7,       7]
osm_pos     = [20,       -5,      20]

avg_total   = round(sum(total_pnl) / 3)
avg_osm     = round(sum(osm_pnl)   / 3)
avg_pep     = round(sum(pep_pnl)   / 3)

# ── Colors ──────
C_TEAL   = "#1D9E75"
C_PURPLE = "#7F77DD"
C_AMBER  = "#BA7517"
C_GRAY   = "#888780"
C_BG     = "#F8F8F6"

fig = plt.figure(figsize=(14, 10), facecolor=C_BG)
fig.suptitle(
    "IMC Prosperity Round 1 — Backtest Results\n"
    "Strategy: OSMIUM mean reversion + PEPPER buy-and-hold",
    fontsize=14, fontweight="bold", y=0.98, color="#2C2C2A"
)

x     = np.arange(len(days))
width = 0.28

# CHART 1: Stacked PnL by product
ax1 = fig.add_subplot(2, 2, 1, facecolor=C_BG)
ax1.bar(x, pep_pnl, width * 2.2, label="PEPPER PnL", color=C_TEAL,   alpha=0.85)
ax1.bar(x, osm_pnl, width * 2.2, label="OSMIUM PnL", color=C_AMBER,  alpha=0.85,
        bottom=pep_pnl)

for i, (o, p) in enumerate(zip(osm_pnl, pep_pnl)):
    ax1.text(x[i], p + o + 200, f"+{o+p:,}", ha="center",
             fontsize=9, fontweight="bold", color="#2C2C2A")
    ax1.text(x[i], p / 2, f"+{p:,}", ha="center",
             fontsize=8, color="white", fontweight="bold")
    ax1.text(x[i], p + o / 2, f"+{o:,}", ha="center",
             fontsize=8, color="white", fontweight="bold")

ax1.axhline(avg_total, color=C_PURPLE, linewidth=1.5,
            linestyle="--", label=f"Avg total: {avg_total:,}")
ax1.set_title("PnL by product per day", fontsize=11, pad=8)
ax1.set_xticks(x); ax1.set_xticklabels(days)
ax1.set_ylabel("PnL")
ax1.set_ylim(0, 42000)
ax1.legend(fontsize=8)
ax1.spines[["top","right"]].set_visible(False)
ax1.set_facecolor(C_BG)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))

# CHART 2: Total PnL line across days
ax2 = fig.add_subplot(2, 2, 2, facecolor=C_BG)
ax2.plot(days, total_pnl, marker="o", linewidth=2.5,
         color=C_TEAL, markersize=8, label="Total PnL")
ax2.fill_between(days, total_pnl, alpha=0.12, color=C_TEAL)
ax2.axhline(avg_total, color=C_PURPLE, linewidth=1.5,
            linestyle="--", label=f"Average: {avg_total:,}")

for i, v in enumerate(total_pnl):
    ax2.annotate(f"+{v:,}", (days[i], v),
                 textcoords="offset points", xytext=(0, 10),
                 ha="center", fontsize=9, fontweight="bold", color="#2C2C2A")

ax2.set_title("Total portfolio value per day", fontsize=11, pad=8)
ax2.set_ylabel("Portfolio Value")
ax2.set_ylim(34000, 37000)
ax2.legend(fontsize=8)
ax2.spines[["top","right"]].set_visible(False)
ax2.set_facecolor(C_BG)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
# CHART 3: Trade count comparison

ax3 = fig.add_subplot(2, 2, 3, facecolor=C_BG)
b1 = ax3.bar(x - width/2, osm_trades, width, label="OSMIUM trades",
             color=C_AMBER, alpha=0.85)
b2 = ax3.bar(x + width/2, pep_trades, width, label="PEPPER trades",
             color=C_TEAL, alpha=0.85)

for bar in b1:
    ax3.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 1,
             str(int(bar.get_height())),
             ha="center", fontsize=9, fontweight="bold", color="#2C2C2A")
for bar in b2:
    ax3.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 1,
             str(int(bar.get_height())),
             ha="center", fontsize=9, fontweight="bold", color="#2C2C2A")

ax3.set_title("Trade count per day", fontsize=11, pad=8)
ax3.set_xticks(x); ax3.set_xticklabels(days)
ax3.set_ylabel("Number of trades")
ax3.legend(fontsize=8)
ax3.spines[["top","right"]].set_visible(False)
ax3.set_facecolor(C_BG)


# CHART 4: Summary comparison table

ax4 = fig.add_subplot(2, 2, 4, facecolor=C_BG)
ax4.axis("off")

table_data = [
    ["Metric",        "Day -1",   "Day 0",    "Day -2",    "Average"],
    ["Total PnL",     "+35,720",  "+35,868",  "+35,293",  f"+{avg_total:,}"],
    ["PEPPER PnL",    "+34,685",  "+34,760",  "+34,822",  f"+{avg_pep:,}"],
    ["OSMIUM PnL",    "+1,035",   "+1,108",   "+471",     f"+{avg_osm:,}"],
    ["OSMIUM trades", "85",       "97",       "54",       f"{round(sum(osm_trades)/3)}"],
    ["PEPPER trades", "7",        "7",        "7",        "7"],
    ["OSM final pos", "+20",      "-5",       "+20",      "+12"],
    ["Status",        "✓ Pass",   "✓ Pass",   "✓ Pass",   "✓ Robust"],
]

col_colors = [
    ["#E1F5EE"] * 5,
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    [C_BG, C_BG, C_BG, C_BG, "#E1F5EE"],
    ["#E1F5EE", "#E1F5EE", "#E1F5EE", "#E1F5EE", "#9FE1CB"],
]

table = ax4.table(
    cellText   = [row for row in table_data],
    cellLoc    = "center",
    loc        = "center",
    cellColours= col_colors,
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.6)

# Style header row
for j in range(5):
    table[0, j].set_text_props(fontweight="bold", color="white")
    table[0, j].set_facecolor(C_TEAL)

ax4.set_title("Full comparison table", fontsize=11, pad=8)

# ── Layout & save ───────
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("backtest_comparison.png", dpi=150,
            bbox_inches="tight", facecolor=C_BG)
plt.show()
print("Chart saved as backtest_comparison.png")
