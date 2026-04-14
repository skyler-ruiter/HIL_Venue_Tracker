"""
generate_ical.py — Export conference deadlines and dates to an iCalendar (.ics) file.

Subscribe to the generated file in Google Calendar, Outlook, or Apple Calendar.
Each deadline includes a 30-day advance reminder.

Usage:
    python generate_ical.py               # tier-1 venues only (default)
    python generate_ical.py --show-all    # include non-tier-1 venues
    python generate_ical.py --output my_deadlines.ics
"""

import argparse
import datetime as dt
from timeline_generator import load_conferences

DEADLINE_REMINDER_DAYS = 30


def fold(line):
    """Fold long lines at 75 octets per RFC 5545."""
    encoded = line.encode('utf-8')
    if len(encoded) <= 75:
        return line
    chunks = []
    while len(encoded) > 75:
        chunks.append(encoded[:75].decode('utf-8'))
        encoded = b' ' + encoded[75:]
    chunks.append(encoded.decode('utf-8'))
    return '\r\n'.join(chunks)


def fmt_date(d):
    return d.strftime('%Y%m%d')


def make_uid(name, event_type, date):
    safe = name.replace(' ', '-').replace('/', '-')
    return f'{safe}-{event_type}-{fmt_date(date)}@hil-venue-tracker'


def vevent(summary, date, description, url, uid, reminder_days=None):
    lines = [
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTART;VALUE=DATE:{fmt_date(date)}',
        f'DTEND;VALUE=DATE:{fmt_date(date + dt.timedelta(days=1))}',
        fold(f'SUMMARY:{summary}'),
        fold(f'DESCRIPTION:{description}'),
    ]
    if url:
        lines.append(fold(f'URL:{url}'))
    if reminder_days:
        lines += [
            'BEGIN:VALARM',
            f'TRIGGER:-P{reminder_days}D',
            'ACTION:DISPLAY',
            fold(f'DESCRIPTION:Reminder: {summary}'),
            'END:VALARM',
        ]
    lines.append('END:VEVENT')
    return lines


def generate_ical(conferences, output_path='deadlines.ics'):
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//HIL Venue Tracker//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:HIL Conference Deadlines',
        'X-WR-CALDESC:HPC conference submission deadlines and event dates',
    ]

    deadline_count = 0
    conf_count = 0

    for conf in conferences:
        if conf['conference'] is None:
            continue

        name      = conf['name']
        full_name = conf['full_name']
        url       = conf['url']

        # One event per deadline, with a 30-day reminder
        for dl in sorted(conf['deadlines'], key=lambda d: d['date']):
            date      = dl['date']
            note      = dl['notes']
            note_part = f' ({note})' if note else ''
            summary   = f'{name} Paper Deadline{note_part}'
            desc      = f'{full_name} submission deadline.{note_part}'
            lines += vevent(summary, date, desc, url,
                            uid=make_uid(name, 'deadline', date),
                            reminder_days=DEADLINE_REMINDER_DAYS)
            deadline_count += 1

        # Conference date — informational event, no reminder
        conf_date = conf['conference']
        lines += vevent(
            summary=f'{name} Conference',
            date=conf_date,
            description=f'{full_name}.',
            url=url,
            uid=make_uid(name, 'conference', conf_date),
        )
        conf_count += 1

    lines.append('END:VCALENDAR')

    with open(output_path, 'w', newline='') as f:
        f.write('\r\n'.join(lines) + '\r\n')

    print(f'Saved to {output_path}')
    print(f'  {deadline_count} deadline events ({DEADLINE_REMINDER_DAYS}-day reminder each)')
    print(f'  {conf_count} conference date events')
    print()
    print('To subscribe:')
    print('  Google Calendar:  Settings > Add calendar > From URL (or import the file)')
    print('  Apple Calendar:   File > Import')
    print('  Outlook:          File > Open & Export > Import/Export')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Export conference deadlines to iCalendar (.ics) format.')
    parser.add_argument('--show-all', action='store_true',
                        help='Include non-tier-1 venues.')
    parser.add_argument('--csv', default='conferences.csv',
                        help='Path to conferences CSV (default: conferences.csv).')
    parser.add_argument('--output', default='deadlines.ics',
                        help='Output file path (default: deadlines.ics).')
    args = parser.parse_args()

    confs = load_conferences(args.csv, tier1_only=not args.show_all)
    generate_ical(confs, output_path=args.output)
