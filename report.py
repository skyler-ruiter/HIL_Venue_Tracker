"""
report.py — Print a text summary of tracked venues with deadlines, notes, and targets.

Usage:
    python report.py                          # tier-1 venues, sorted by earliest deadline
    python report.py --show-all               # include non-tier-1 venues (shown dimmed)
    python report.py --approx                 # only venues with approximate dates
    python report.py --next 5                 # 5 nearest upcoming deadlines (quick view)
    python report.py --since 2026-10-01       # deadlines on or after this date
    python report.py --until 2026-12-31       # deadlines on or before this date
    python report.py --since 2026-10-01 --until 2026-12-31
"""

import csv
import datetime as dt
import argparse
from timeline_generator import BASE_YEAR, load_conferences

APPROX_FLAG = 'approximate'

# Terminal color codes
RESET  = '\033[0m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
RED    = '\033[31m'
YELLOW = '\033[33m'
GREEN  = '\033[32m'


def load_targets(path='targets.csv'):
    targets = {}
    try:
        with open(path, newline='') as f:
            for row in csv.DictReader(f):
                venue = row['venue'].strip()
                targets.setdefault(venue, []).append({
                    'paper': row.get('paper', '').strip(),
                    'notes': row.get('notes', '').strip(),
                })
    except FileNotFoundError:
        pass
    return targets


def fmt_date(d):
    return d.strftime('%b %-d, %Y')


def is_approximate(conf):
    return APPROX_FLAG in conf.get('notes', '').lower()


def urgency_marker(days_away):
    if days_away < 0:
        return f'{DIM}[passed]{RESET}'
    elif days_away <= 30:
        return f'{RED}[in {days_away}d]{RESET}'
    elif days_away <= 60:
        return f'{YELLOW}[in {days_away}d]{RESET}'
    else:
        return f'{DIM}[in {days_away}d]{RESET}'


def print_next(conferences, n, targets):
    """Print the N nearest upcoming deadlines as a compact flat list."""
    today = dt.date.today()

    upcoming = []
    for conf in conferences:
        for dl in conf['deadlines']:
            if dl['date'] >= today:
                upcoming.append({
                    'name':   conf['name'],
                    'tier':   conf['tier'],
                    'tier1':  conf['tier1'],
                    'date':   dl['date'],
                    'note':   dl['notes'],
                    'url':    conf['url'],
                    'approx': is_approximate(conf),
                    'targeted': conf['name'] in targets,
                    'accept': conf.get('acceptance_rate', ''),
                })
    upcoming.sort(key=lambda d: d['date'])
    upcoming = upcoming[:n]

    if not upcoming:
        print(f'\n{DIM}No upcoming deadlines found.{RESET}\n')
        return

    header = f'Next {len(upcoming)} upcoming deadline{"s" if len(upcoming) != 1 else ""}'
    print()
    print(BOLD + header + RESET)
    print(DIM + '─' * 60 + RESET)

    for d in upcoming:
        days_away  = (d['date'] - today).days
        short_note = d['note'] if len(d['note']) <= 14 else ''
        note_part  = f'  {DIM}({short_note}){RESET}' if short_note else ''
        approx_tag = f' {YELLOW}~{RESET}' if d['approx'] else ''
        target_tag = f' {GREEN}★{RESET}' if d['targeted'] else ''
        accept     = f'  {DIM}{d["accept"]}{RESET}' if d['accept'] else ''
        print(f'  {fmt_date(d["date"])}  {BOLD}{d["name"]:<14}{RESET}'
              f'{urgency_marker(days_away)}{note_part}{approx_tag}{target_tag}{accept}')

    print()
    print(f'{DIM}★ = targeted in targets.csv  ~ = approximate date{RESET}')
    print()


def print_report(conferences, targets, show_all=False, approx_only=False,
                 since=None, until=None):
    today = dt.date.today()

    conferences = [c for c in conferences if c['conference'] is not None]

    # Apply --since / --until: keep only venues with at least one deadline in the window
    if since or until:
        def in_window(dl_date):
            if since and dl_date < since:
                return False
            if until and dl_date > until:
                return False
            return True
        conferences = [
            c for c in conferences
            if any(in_window(dl['date']) for dl in c['deadlines'])
        ]
        # Also trim each venue's deadline list to the window
        for c in conferences:
            c['deadlines'] = [dl for dl in c['deadlines'] if in_window(dl['date'])]

    conferences.sort(key=lambda c: min(d['date'] for d in c['deadlines']) if c['deadlines'] else c['conference'])

    if approx_only:
        conferences = [c for c in conferences if is_approximate(c)]

    # Build header
    parts = []
    if approx_only:
        parts.append('approximate dates only')
    elif not show_all:
        parts.append('tier-1 only')
    else:
        parts.append('all venues')
    if since:
        parts.append(f'from {since}')
    if until:
        parts.append(f'until {until}')
    header = f'Conference Report  ({BASE_YEAR - 1}–{BASE_YEAR})  [{", ".join(parts)}]'

    print()
    print(BOLD + '=' * len(header) + RESET)
    print(BOLD + header + RESET)
    print(BOLD + '=' * len(header) + RESET)
    print(f'{DIM}Sorted by earliest deadline  |  today: {fmt_date(today)}{RESET}')
    print()

    for conf in conferences:
        name          = conf['name']
        tier1         = conf['tier1']
        tier          = conf['tier'].upper()
        full_name     = conf['full_name']
        url           = conf['url']
        notes         = conf.get('notes', '')
        notes_file    = conf.get('notes_file', '')
        accept        = conf.get('acceptance_rate', '')
        approx        = is_approximate(conf)
        venue_targets = targets.get(name, [])

        deadlines = sorted(conf['deadlines'], key=lambda d: d['date'])
        conf_date = conf['conference']

        prefix = DIM if (show_all and not tier1) else ''
        suffix = RESET if prefix else ''

        approx_label = f' {YELLOW}[APPROX — verify dates]{RESET}' if approx else ''
        tier1_label  = '' if tier1 else f' {DIM}(non-tier-1){RESET}'
        accept_label = f'  {DIM}acceptance ~{accept.lstrip("~")}{RESET}' if accept else ''

        print(prefix + BOLD + f'[{tier}]' + RESET +
              prefix + f'  {name} — {full_name}' + suffix +
              approx_label + tier1_label + accept_label)

        for dl in deadlines:
            date     = dl['date']
            dl_note  = dl['notes']
            days     = (date - today).days
            note_sfx = f'  {DIM}({dl_note}){RESET}' if dl_note else ''
            print(prefix + f'  Deadline:    {fmt_date(date)}  {urgency_marker(days)}' +
                  note_sfx + suffix)

        conf_days = (conf_date - today).days
        print(prefix + f'  Conference:  {fmt_date(conf_date)}  {urgency_marker(conf_days)}' + suffix)

        if url:
            print(prefix + f'  URL:         {url}' + suffix)
        if notes:
            print(prefix + f'  Notes:       {notes}' + suffix)
        if notes_file:
            print(prefix + f'  Details:     {notes_file}' + suffix)

        for t in venue_targets:
            line = f'  {GREEN}>> Targeting:{RESET} {BOLD}{t["paper"]}{RESET}'
            if t['notes']:
                line += f'  —  {t["notes"]}'
            print(line)

        print()

    print(f'{DIM}Generated {dt.datetime.now().strftime("%Y-%m-%d %H:%M")}  |  BASE_YEAR={BASE_YEAR}{RESET}')
    print()


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid date "{s}" — use YYYY-MM-DD format.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print a venue summary with deadlines and targets.')
    parser.add_argument('--show-all', action='store_true',
                        help='Include non-tier-1 venues.')
    parser.add_argument('--approx', action='store_true',
                        help='Only show venues with approximate dates.')
    parser.add_argument('--next', metavar='N', type=int,
                        help='Show only the N nearest upcoming deadlines (compact view).')
    parser.add_argument('--since', metavar='YYYY-MM-DD', type=parse_date,
                        help='Only show deadlines on or after this date.')
    parser.add_argument('--until', metavar='YYYY-MM-DD', type=parse_date,
                        help='Only show deadlines on or before this date.')
    parser.add_argument('--csv', default='conferences.csv',
                        help='Path to conferences CSV (default: conferences.csv).')
    parser.add_argument('--targets', default='targets.csv',
                        help='Path to targets CSV (default: targets.csv).')
    args = parser.parse_args()

    confs   = load_conferences(args.csv, tier1_only=not args.show_all)
    targets = load_targets(args.targets)

    if args.next:
        print_next(confs, args.next, targets)
    else:
        print_report(confs, targets, show_all=args.show_all, approx_only=args.approx,
                     since=args.since, until=args.until)
