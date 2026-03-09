from typing import Dict, List


CaseStudy = Dict[str, object]


CASE_STUDIES: List[CaseStudy] = [
    {
        'slug': 'executive-kpi-monitoring',
        'title': 'Executive KPI Monitoring Across Client App Ecosystems',
        'problem_line': 'Built recurring product and business KPI monitoring across DAU, memberships, revenue, notifications, auctions, livestreams, and timeline activity.',
        'highlights': [
            'Multi-metric time-series dashboard with event overlays.',
            'Supports weekly product and leadership review.',
            'Helps diagnose trend shifts and intervention effects.',
        ],
        'homepage_caption': 'Operating dashboard used to monitor business and product movement across a multi-client app portfolio.',
        'thumbnail_src': '/assets/case_studies/executive-kpi-monitoring.jpg',
        'thumbnail_alt': 'Dashboard showing DAU and memberships with event overlays and summary statistics.',
        'image_caption': 'A dual-axis KPI monitor linking user activity, memberships, and event timelines for weekly product and leadership reviews.',
        'overview': (
            'Built a production KPI monitoring surface for a white-label app ecosystem where leadership needed '
            'daily visibility into product health and monetization movement.'
        ),
        'business_problem': (
            'Core metrics lived in separate pipelines and ad-hoc reports, making trend diagnosis slow and '
            'decision-making inconsistent across client accounts.'
        ),
        'data_inputs': [
            'Daily product event logs (notifications, auctions, livestreams, timeline posts).',
            'Membership and subscription status snapshots.',
            'Revenue records from recurring app monetization flows.',
            'Client-level filters and date-window controls for multi-tenant analysis.',
        ],
        'what_i_built': [
            'Defined metric contracts for DAU, memberships, downloads, new memberships, and revenue.',
            'Implemented multi-axis charting with event overlays to contextualize spikes and declines.',
            'Added aggregated summary tables for quick mean/min/max/total diagnostics.',
            'Shipped date-range and client selectors for leadership and PM review workflows.',
        ],
        'methods': [
            'Metric normalization and daily aggregation pipelines.',
            'Comparative time-series monitoring with event annotation.',
            'Segmented filtering by account context to isolate client-level behavior.',
        ],
        'impact': [
            'Reduced ambiguity in KPI discussions by giving leadership one shared source of truth.',
            'Enabled faster root-cause conversations around membership and usage swings.',
            'Supported recurring operating reviews with decision-ready, not raw, analytics.',
        ],
        'tools': ['Python', 'SQL', 'Dash/Plotly', 'Pandas/Polars', 'Flask', 'Celery'],
    },
    {
        'slug': 'behavior-geography-correlation',
        'title': 'Behavior, Geography, and Correlation Diagnostics',
        'problem_line': 'Built analysis views to connect user behavior, memberships, content activity, and geographic distribution into decision-ready diagnostics.',
        'highlights': [
            'Correlation analysis across engagement and monetization signals.',
            'Geography and user-segmentation views.',
            'Used to identify patterns, weak signals, and business-relevant relationships.',
        ],
        'homepage_caption': 'Integrated diagnostics view combining behavior, geography, and relationship analysis for product triage.',
        'thumbnail_src': '/assets/case_studies/behavior-geography-correlation.jpg',
        'thumbnail_alt': 'Dashboard with user location bars, DAU versus memberships scatter plot, and correlation matrix.',
        'image_caption': 'Diagnostics panel combining top user locations, DAU-membership relationships, and correlation structure across product events.',
        'overview': (
            'Designed an exploratory diagnostics dashboard to move from isolated KPI checks to relationship-level '
            'analysis across behavior, engagement, and monetization signals.'
        ),
        'business_problem': (
            'Teams could see top-line movement but lacked reliable diagnostics to evaluate whether activity changes '
            'were noise, weak signals, or meaningful product patterns.'
        ),
        'data_inputs': [
            'Daily active user and membership time-series.',
            'Location-level user aggregates (city and region views).',
            'Event volume streams for timeline posts, notifications, and downloads.',
        ],
        'what_i_built': [
            'Implemented location distribution charts with client/date/user-type filtering.',
            'Created scatter diagnostics with regression overlays for DAU-membership relationship analysis.',
            'Added a correlation matrix for quick scanning of directional relationships across event families.',
        ],
        'methods': [
            'Correlation diagnostics and relationship triage.',
            'Segment-level slicing to detect outliers and concentration effects.',
            'Cross-metric pattern checks to separate coincidence from repeatable trends.',
        ],
        'impact': [
            'Gave PMs a practical way to prioritize experiments around high-signal behaviors.',
            'Improved quality of product discussions by grounding hypotheses in comparative diagnostics.',
            'Surfaced non-obvious relationships to guide follow-up analysis and rollout thinking.',
        ],
        'tools': ['Python', 'SQL', 'Dash/Plotly', 'Statistical Diagnostics', 'Pandas'],
    },
    {
        'slug': 'geo-segmented-user-intelligence',
        'title': 'Geo-Segmented User Intelligence',
        'problem_line': 'Built user-distribution views to understand where users are concentrated and how account or membership segments differ geographically.',
        'highlights': [
            'Map-based user distribution analysis.',
            'Segmentation by user/account type.',
            'Supports audience understanding and regional strategy discussions.',
        ],
        'homepage_caption': 'Geo-intelligence map used to compare audience concentration and segment mix across regions.',
        'thumbnail_src': '/assets/case_studies/geo-segmented-user-intelligence.jpg',
        'thumbnail_alt': 'Dark map of the United States showing geo-distributed user points by account type.',
        'image_caption': 'Geo-segmented user map used to compare concentration, spread, and segment mix across regions.',
        'overview': (
            'Built a geo-intelligence layer so product stakeholders could quickly understand audience distribution '
            'and segment density across the U.S. footprint.'
        ),
        'business_problem': (
            'User distribution insight was fragmented and hard to compare across account types, which limited '
            'regional planning and launch sequencing decisions.'
        ),
        'data_inputs': [
            'User-level location records from app activity and account metadata.',
            'Account segmentation flags (not signed-up, signed-up, member, super user).',
            'Client-level controls for filtered market views.',
        ],
        'what_i_built': [
            'Shipped a map-based user intelligence dashboard with segment color coding and layer controls.',
            'Standardized location and segment logic so counts were comparable across clients.',
            'Added interfaces to inspect regional density and identify concentration corridors.',
        ],
        'methods': [
            'Geo-segmentation and density inspection.',
            'Category-level distribution comparison by account type.',
            'Market spread diagnostics for rollout and targeting conversations.',
        ],
        'impact': [
            'Made geographic concentration visible for stakeholder planning and prioritization.',
            'Improved confidence in regional targeting decisions with segment-aware map evidence.',
            'Provided a reusable geo lens for ongoing growth and product strategy reviews.',
        ],
        'tools': ['Python', 'SQL', 'Dash/Plotly Map Layers', 'Geo Analytics', 'Data Modeling'],
    },
]
