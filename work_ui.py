"""Shared vocabulary for presenting work items.

One list, one card, one set of metadata fields, used by the home page, the
project index and the case-study pages. Keeping the ordering and the card here
is what stops the three surfaces from disagreeing about what a project is
called, what came of it, or where it sits in the sequence.
"""

from typing import List, Optional

from dash import html

from case_studies import CASE_STUDIES, LIVE_DEMO, RESEARCH_HIGHLIGHTS


# Canonical order: the live demo leads because it is the only item whose
# software this repository actually contains, then product work, then research.
WORK: List[dict] = [LIVE_DEMO] + CASE_STUDIES + RESEARCH_HIGHLIGHTS

# The four the home page shows as secondary cards beside the featured one. The
# home page is a summary, not an inventory — the index carries all seven.
HOME_SECONDARY = ['executive-kpi-monitoring', 'geo-segmented-user-intelligence',
                  'lidar-benchmark-engineering', 'volumetric-3d-vision-evaluation']

FEATURED_SLUG = 'tidepool-commerce-analytics'


def by_slug(slug: str) -> dict:
    for item in WORK:
        if item['slug'] == slug:
            return item
    raise KeyError(slug)


def detail_href(item) -> str:
    return f"/projects/{item['slug']}"


def is_research(item) -> bool:
    return item['scope'].startswith('AI / ML')


def outcome(item) -> str:
    """The one sentence a card promises.

    The first impact line for a case study; the live demo has no impact list, so
    it uses the summary it is introduced with everywhere else.
    """
    impact = item.get('impact')
    return impact[0] if impact else item['problem_line']


def neighbours(slug: str):
    """The previous and next work item, as a ring so no page is a dead end."""
    index = [i['slug'] for i in WORK].index(slug)
    return WORK[index - 1], WORK[(index + 1) % len(WORK)]


def tags(item, limit: Optional[int] = None):
    values = item['tags'][:limit] if limit else item['tags']
    return html.Div(
        className='skill-cloud',
        children=[html.Span(tag, className='skill-pill') for tag in values],
    )


def work_card(item, *, track_location: str, tag_limit: int = 3,
              link_label: str = 'Read case study', heading=html.H3):
    """A work card: category, title, outcome, role and year, tags, a way in.

    The whole card is the link, and every surface uses this one — so a project
    reads the same on the home page as it does in the index.

    `heading` is the level the title takes, because the same card sits at two
    depths: under the "Selected Work" H2 on the home page, and directly under
    the page H1 on the index, where an H3 would skip a level.
    """
    card_class = 'glass-card card-hover work-card'
    if is_research(item):
        card_class += ' work-card--research'

    return html.A(
        href=detail_href(item),
        className=card_class,
        **{
            'data-track': 'work_card_click',
            'data-track-location': track_location,
            'data-track-label': item['slug'],
        },
        children=[
            html.Div(item['scope'], className='project-scope'),
            heading(item['title'], className='work-card-title'),
            html.P(outcome(item), className='work-card-outcome'),
            html.Div(
                className='work-card-meta',
                children=[
                    html.Span(item['role'], className='work-card-role'),
                    html.Span(item['period'], className='work-card-period'),
                ],
            ),
            tags(item, tag_limit),
            html.Span(link_label, className='work-card-link'),
        ],
    )
