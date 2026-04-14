import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import datetime as dt
import csv
import argparse
from matplotlib.lines import Line2D

BASE_YEAR = 2027

TIER_COLORS = {
    'top':      '#c0392b',  # dark red
    'regular':  '#2980b9',  # blue
    'workshop': '#7f8c8d',  # gray
}

NON_TIER1_ALPHA = 0.28


def load_conferences(csv_path, tier1_only=True):
    conferences = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            is_tier1 = row['tier1'].strip().lower() == 'true'
            if tier1_only and not is_tier1:
                continue
            if name not in conferences:
                conferences[name] = {
                    'name': name,
                    'full_name': row.get('full_name', name),
                    'tier': row['tier'],
                    'tier1': is_tier1,
                    'deadlines': [],
                    'conference': None,
                    'url': row.get('url', ''),
                    'notes': row.get('notes', ''),
                    'notes_file': row.get('notes_file', ''),
                    'acceptance_rate': row.get('acceptance_rate', ''),
                }
            year = BASE_YEAR + int(row['year_offset'])
            date = dt.date(year, int(row['month']), int(row['day']))
            if row['event_type'] == 'conference':
                conferences[name]['conference'] = date
            else:
                conferences[name]['deadlines'].append({
                    'date': date,
                    'notes': row.get('notes', '').strip(),
                })
    return list(conferences.values())


def plot_timeline(conferences, output_path='conference_timeline.png', show_all=False, show=True):
    conferences = [c for c in conferences if c['conference'] is not None]
    conferences.sort(key=lambda c: min(d['date'] for d in c['deadlines']) if c['deadlines'] else c['conference'])
    n = len(conferences)

    fig, ax = plt.subplots(figsize=(18, max(6, n * 0.6 + 2)))

    span_start = dt.date(BASE_YEAR - 1, 1, 1)
    year_boundary = dt.date(BASE_YEAR, 1, 1)
    span_end = dt.date(BASE_YEAR, 12, 31)

    # Shade the pre-year
    ax.axvspan(span_start, year_boundary, alpha=0.07, color='#e67e22', zorder=0)

    # Year boundary
    ax.axvline(year_boundary, color='#555', linewidth=1.5, linestyle='--', alpha=0.6, zorder=1)

    # Year labels at top
    ax.text(dt.date(BASE_YEAR - 1, 7, 1), n + 0.1, f'{BASE_YEAR - 1}  (pre-year)',
            ha='center', va='bottom', fontsize=11, color='#7d6608', alpha=0.8)
    ax.text(dt.date(BASE_YEAR, 7, 1), n + 0.1, f'{BASE_YEAR}  (main year)',
            ha='center', va='bottom', fontsize=11, color='#333', alpha=0.8)

    for i, conf in enumerate(conferences):
        color = TIER_COLORS[conf['tier']]
        alpha = 1.0 if conf['tier1'] else NON_TIER1_ALPHA
        deadlines = sorted(conf['deadlines'], key=lambda d: d['date'])
        conf_date = conf['conference']

        # Span line from earliest deadline to conference date
        if deadlines:
            ax.hlines(i, deadlines[0]['date'], conf_date, colors=color, linewidth=2.5,
                      alpha=0.3 * alpha, zorder=2)

        # Deadline markers + date label above + short note below
        for dl in deadlines:
            date  = dl['date']
            note  = dl['notes']
            ax.scatter(date, i, color=color, marker='D', s=65, zorder=4,
                       edgecolors='white', linewidths=0.5, alpha=alpha)
            ax.text(date, i + 0.22, date.strftime('%-m/%-d'),
                    ha='center', va='bottom', fontsize=6.5, color=color, zorder=5,
                    alpha=alpha)
            if note and len(note) <= 14:
                ax.text(date, i - 0.22, note,
                        ha='center', va='top', fontsize=5.5, color=color, zorder=5,
                        alpha=alpha * 0.85, style='italic')

        # Conference marker
        ax.scatter(conf_date, i, color=color, marker='*', s=280, zorder=4,
                   edgecolors='white', linewidths=0.5, alpha=alpha)

    # Y axis — bold labels for tier-1, normal for others
    ax.set_yticks(range(n))
    labels = ax.set_yticklabels([c['name'] for c in conferences], fontsize=10)
    for label, conf in zip(labels, conferences):
        label.set_alpha(1.0 if conf['tier1'] else NON_TIER1_ALPHA + 0.1)

    ax.set_ylim(-0.6, n + 0.2)

    # X axis: every month
    ax.set_xlim(span_start, span_end)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)

    # Vertical grid lines at each month
    ax.xaxis.grid(True, alpha=0.2, linestyle=':')
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)

    # Today marker
    today = dt.date.today()
    if span_start <= today <= span_end:
        ax.axvline(today, color='green', linewidth=1.2, linestyle=':', alpha=0.8, zorder=3)
        ax.text(today, -0.55, 'today', ha='center', va='top', fontsize=7,
                color='green', alpha=0.9)

    # Legend
    legend_elements = [
        mpatches.Patch(color=TIER_COLORS['top'],      label='Top Conference'),
        mpatches.Patch(color=TIER_COLORS['regular'],  label='Regular Conference'),
        mpatches.Patch(color=TIER_COLORS['workshop'], label='Workshop'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#555',
               label='Paper Deadline', markersize=8),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#555',
               label='Conference Date', markersize=12),
    ]
    if show_all:
        legend_elements.append(
            mpatches.Patch(color='#aaa', alpha=NON_TIER1_ALPHA + 0.1, label='Non-Tier-1 (faded)')
        )
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8,
              framealpha=0.9, edgecolor='#ccc')

    title_suffix = '  [all venues]' if show_all else '  [tier-1 only]'
    ax.set_title(
        f'Conference Submission & Event Timeline  ({BASE_YEAR - 1}–{BASE_YEAR}){title_suffix}',
        fontsize=13, fontweight='bold', pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f'Saved to {output_path}')
    if show:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a conference submission and event timeline.')
    parser.add_argument(
        '--show-all', action='store_true',
        help='Include non-tier-1 venues (shown faded). Default: tier-1 only.')
    parser.add_argument(
        '--csv', default='conferences.csv',
        help='Path to the conferences CSV (default: conferences.csv).')
    parser.add_argument(
        '--output', default='conference_timeline.png',
        help='Output image path (default: conference_timeline.png).')
    parser.add_argument(
        '--no-show', action='store_true',
        help='Save the image without opening a viewer (useful for CI/headless use).')
    args = parser.parse_args()

    confs = load_conferences(args.csv, tier1_only=not args.show_all)
    plot_timeline(confs, output_path=args.output, show_all=args.show_all,
                  show=not args.no_show)
