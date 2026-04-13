from typing import Dict, List


WorkItem = Dict[str, object]


CASE_STUDIES: List[WorkItem] = [
    {
        'slug': 'executive-kpi-monitoring',
        'scope': 'PRODUCT ANALYTICS / DECISION SYSTEMS',
        'title': 'Executive KPI Monitoring Across Client App Ecosystems',
        'problem_line': 'Built a multi-tenant KPI operating system spanning engagement, retention, memberships, monetization, notifications, auctions, livestreams, and timeline activity.',
        'highlights': [
            'Metric contracts and time-series monitoring for leadership review.',
            'Event overlays and diagnostics for release, campaign, and intervention analysis.',
            'Reusable decision surface for product, growth, and executive operating cadence.',
        ],
        'tags': ['KPI Architecture', 'Decision Systems', 'Monetization', 'Release Diagnostics'],
        'homepage_caption': 'Decision-ready analytics operating layer for a 138-client app ecosystem.',
        'thumbnail_src': '/assets/case_studies/executive-kpi-monitoring.jpg',
        'thumbnail_alt': 'Dashboard showing DAU and memberships with event overlays and summary statistics.',
        'image_caption': 'A dual-axis KPI monitor linking user activity, memberships, and event timelines for weekly product and leadership reviews.',
        'overview': (
            'Built a production KPI monitoring surface for a white-label app ecosystem where leadership needed '
            'daily visibility into product health, operational movement, and revenue signals.'
        ),
        'problem_statement': (
            'Core metrics lived in separate pipelines and ad-hoc reports, making trend diagnosis slow and '
            'decision-making inconsistent across client accounts.'
        ),
        'data_inputs': [
            'Daily product event logs spanning notifications, auctions, livestreams, timeline posts, and downloads.',
            'Membership and subscription status snapshots.',
            'Revenue records from recurring app monetization flows.',
            'Client-level filters and date-window controls for multi-tenant analysis.',
        ],
        'what_i_built': [
            'Defined metric contracts for DAU, memberships, downloads, new memberships, and revenue.',
            'Implemented multi-axis charting with event overlays to contextualize spikes and declines.',
            'Added summary tables for quick mean/min/max/total diagnostics.',
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
            'Turned fragmented reporting into a repeatable decision system rather than one-off dashboards.',
        ],
        'tools': ['Python', 'SQL', 'Dash/Plotly', 'Pandas/Polars', 'Flask', 'Celery'],
    },
    {
        'slug': 'behavior-geography-correlation',
        'scope': 'PRODUCT ANALYTICS / DECISION SYSTEMS',
        'title': 'Behavior, Geography, and Correlation Diagnostics',
        'problem_line': 'Built exploratory diagnostics to connect user behavior, memberships, geography, and engagement relationships into decision-ready analysis.',
        'highlights': [
            'Correlation analysis across engagement, content, and monetization signals.',
            'Geography and user-segmentation views for pattern triage.',
            'Used to separate weak noise from repeatable product-relevant relationships.',
        ],
        'tags': ['Behavioral Analytics', 'Correlation Diagnostics', 'Segmentation', 'Geo Analysis'],
        'homepage_caption': 'Integrated diagnostic layer for product triage, hypothesis generation, and follow-up analysis.',
        'thumbnail_src': '/assets/case_studies/behavior-geography-correlation.jpg',
        'thumbnail_alt': 'Dashboard with user location bars, DAU versus memberships scatter plot, and correlation matrix.',
        'image_caption': 'Diagnostics panel combining top user locations, DAU-membership relationships, and correlation structure across product events.',
        'overview': (
            'Designed an exploratory diagnostics dashboard to move from isolated KPI checks to relationship-level '
            'analysis across behavior, engagement, and monetization signals.'
        ),
        'problem_statement': (
            'Teams could see top-line movement but lacked reliable diagnostics to evaluate whether activity changes '
            'were noise, weak signals, or meaningful product patterns.'
        ),
        'data_inputs': [
            'Daily active user and membership time-series.',
            'Location-level user aggregates with city and region views.',
            'Event volume streams for timeline posts, notifications, downloads, and related engagement activity.',
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
            'Improved product discussions by grounding hypotheses in comparative diagnostics.',
            'Surfaced non-obvious relationships to guide follow-up analysis and rollout thinking.',
        ],
        'tools': ['Python', 'SQL', 'Dash/Plotly', 'Statistical Diagnostics', 'Pandas'],
    },
    {
        'slug': 'geo-segmented-user-intelligence',
        'scope': 'PRODUCT ANALYTICS / DECISION SYSTEMS',
        'title': 'Geo-Segmented User Intelligence',
        'problem_line': 'Built geo-distribution and segment analysis views to understand where users are concentrated and how membership and account mixes differ geographically.',
        'highlights': [
            'Map-based user distribution analysis.',
            'Segmentation by user and account type.',
            'Supports market concentration, rollout, and audience strategy discussions.',
        ],
        'tags': ['Geo Analytics', 'Audience Intelligence', 'Segmentation', 'Data Visualization'],
        'homepage_caption': 'Geographic intelligence layer for segment-aware audience analysis across regions.',
        'thumbnail_src': '/assets/case_studies/geo-segmented-user-intelligence.jpg',
        'thumbnail_alt': 'Dark map of the United States showing geo-distributed user points by account type.',
        'image_caption': 'Geo-segmented user map used to compare concentration, spread, and segment mix across regions.',
        'overview': (
            'Built a geo-intelligence layer so product stakeholders could quickly understand audience distribution '
            'and segment density across the U.S. footprint.'
        ),
        'problem_statement': (
            'User distribution insight was fragmented and hard to compare across account types, which limited '
            'regional planning and launch sequencing decisions.'
        ),
        'data_inputs': [
            'User-level location records from app activity and account metadata.',
            'Account segmentation flags such as non-signed-up, signed-up, member, and super user.',
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


RESEARCH_HIGHLIGHTS: List[WorkItem] = [
    {
        'slug': 'lidar-benchmark-engineering',
        'scope': 'AI / ML / RESEARCH WORK',
        'title': 'LiDAR Benchmark and Annotation Pipeline Engineering',
        'problem_line': 'Built reproducible airborne LiDAR dataset, annotation, and benchmark workflows for single-tree detection and 3D perception research.',
        'highlights': [
            'Produced 5,000+ benchmark-grade tree annotations with QA workflows.',
            'Defined benchmark splits, metadata structure, and repeatable evaluation inputs.',
            'Turned fragmented academic processing into reusable research infrastructure.',
        ],
        'tags': ['LiDAR', 'Point Clouds', 'Dataset Engineering', 'Benchmark Design'],
        'homepage_caption': 'Research infrastructure spanning data curation, annotation design, benchmark construction, and evaluation protocol definition.',
        'overview': (
            'Built the research data backbone for AUSM Lab work on airborne LiDAR tree detection, turning raw point '
            'clouds into benchmark-ready corpora and reproducible evaluation assets.'
        ),
        'problem_statement': (
            'The field lacked public, benchmark-grade datasets and evaluation consistency, which made model comparison '
            'noisy and hard to defend.'
        ),
        'data_inputs': [
            'Airborne LiDAR point clouds and derived volumetric representations.',
            'Annotation workflows for tree instance labeling and quality assurance.',
            'Benchmark splits, metadata schemas, and evaluation artifacts.',
        ],
        'what_i_built': [
            'Designed annotation conventions and QA loops for 5,000+ single-tree labels.',
            'Structured benchmark datasets and reproducible split logic for model evaluation.',
            'Documented preprocessing and experiment assets so research results were traceable and publication-ready.',
        ],
        'methods': [
            '3D point cloud preprocessing and volumetric feature construction.',
            'Dataset curation, annotation QA, and benchmark protocol design.',
            'Evaluation pipeline design for repeatable detection benchmarking.',
        ],
        'impact': [
            'Supported peer-reviewed outputs at ICPR 2022 and downstream dataset work.',
            'Reduced ambiguity in model comparison by standardizing data and evaluation inputs.',
            'Created reusable research infrastructure instead of one-off experiments.',
        ],
        'tools': ['Python', 'NumPy', 'Pandas', 'LiDAR / Point Cloud Processing', 'Annotation QA', 'Benchmark Design'],
    },
    {
        'slug': 'volumetric-3d-vision-evaluation',
        'scope': 'AI / ML / RESEARCH WORK',
        'title': '3D Vision Experimentation for Detection and Comparative Model Analysis',
        'problem_line': 'Designed and evaluated deep learning workflows for detecting individual trees from airborne LiDAR using 3D and volumetric representations.',
        'highlights': [
            'Worked across model design, data representation, and evaluation setup.',
            'Compared model behavior across input formulations and thresholds.',
            'Connected experiment outputs to thesis and publication-grade technical synthesis.',
        ],
        'tags': ['3D Vision', 'Deep Learning', 'Detection', 'Model Evaluation'],
        'homepage_caption': 'Applied ML research work spanning model experimentation, error analysis, and evaluation methodology.',
        'overview': (
            'Worked across model development, experiment design, and comparative evaluation for single-tree '
            'detection from airborne LiDAR data.'
        ),
        'problem_statement': (
            'Detection performance was sensitive to representation choice, data quality, and evaluation setup, '
            'requiring careful experimentation rather than isolated model runs.'
        ),
        'data_inputs': [
            'Airborne LiDAR point clouds and voxelized or volumetric inputs.',
            'Instance-level benchmark annotations and split definitions.',
            'Comparative experiment outputs, metrics, and qualitative error cases.',
        ],
        'what_i_built': [
            'Ran deep learning experiment workflows for single-tree detection using volumetric CNN-based approaches.',
            'Compared model behavior across input representations, thresholds, and evaluation settings.',
            'Synthesized results into defendable research narratives, technical reporting, and thesis outputs.',
        ],
        'methods': [
            '3D computer vision experimentation and representation design.',
            'Comparative model analysis and qualitative error inspection.',
            'Precision/recall-oriented detection evaluation and benchmark reporting.',
        ],
        'impact': [
            'Produced thesis work awarded Best Master\'s Thesis at York University.',
            'Strengthened the lab\'s basis for model selection and follow-on dataset research.',
            'Expanded my profile beyond analytics into applied ML research and experiment design.',
        ],
        'tools': ['Python', 'Deep Learning Research', '3D Computer Vision', 'Evaluation Metrics', 'Experimentation', 'Research Synthesis'],
    },
    {
        'slug': 'segmentation-scene-understanding',
        'scope': 'AI / ML / RESEARCH WORK',
        'title': 'Segmentation and Scene-Understanding Benchmark Analysis',
        'problem_line': 'Contributed to dataset and evaluation work supporting semantic segmentation and scene-understanding research on large-scale aerial LiDAR data.',
        'highlights': [
            'Connected dataset design with segmentation-oriented model evaluation.',
            'Framed point cloud labeling around scene understanding, not only detection.',
            'Emphasized benchmark quality, comparability, and methodological clarity.',
        ],
        'tags': ['Semantic Segmentation', 'Scene Understanding', 'Perception', 'Research Methodology'],
        'homepage_caption': 'Segmentation-oriented research support spanning data design, evaluation framing, and technical synthesis.',
        'overview': (
            'Extended research work from instance detection into segmentation-oriented dataset thinking for aerial '
            'LiDAR and urban forest scene understanding.'
        ),
        'problem_statement': (
            'Segmentation research needed richer labeled point cloud corpora and clearer evaluation framing to '
            'support reproducible comparison across methods.'
        ),
        'data_inputs': [
            'Large-scale aerial LiDAR scenes with semantic class structure.',
            'Annotation schemas, preprocessing decisions, and benchmark metadata.',
            'Paper synthesis across segmentation and perception literature.',
        ],
        'what_i_built': [
            'Supported dataset and evaluation framing for segmentation-focused LiDAR research.',
            'Analyzed tradeoffs around label quality, class definitions, and benchmark comparability.',
            'Translated technical findings into concise research communication for publication support.',
        ],
        'methods': [
            'Semantic segmentation benchmark analysis.',
            'Point cloud labeling strategy and dataset quality review.',
            'Research synthesis across 3D perception and scene-understanding literature.',
        ],
        'impact': [
            'Helped broaden lab work from detection into segmentation-oriented research outputs.',
            'Improved clarity around how dataset design influences downstream model evaluation.',
            'Added visible signal in perception, scene understanding, and research methodology.',
        ],
        'tools': ['Python', 'LiDAR Data Engineering', 'Semantic Segmentation', '3D Perception', 'Benchmark Analysis', 'Research Writing'],
    },
]
