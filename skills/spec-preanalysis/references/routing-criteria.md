# Routing criteria

## Split into several specifications when

- outcomes can be accepted, handed off or stopped independently;
- different user groups have independent journeys and business rules;
- lifecycle and data ownership boundaries are stable;
- one article would require several unrelated goals or acceptance decisions;
- dependencies can be expressed as a small acyclic graph.

Do not split only because work has backend/frontend parts, several screens, several
agents, many requirements, or different implementation repositories.

## Choose article-first when

- there is one dominant end-to-end journey;
- most rules or terms are shared across all sections;
- the working article fits comfortably in one bounded context;
- parallel work would create more coordination than useful independence.

## Choose hybrid when

- at least two semantic concerns can be analyzed from bounded source subsets;
- their interfaces can be stated explicitly;
- parallel work shortens real analysis rather than duplicating common context;
- integration after each of four stages is affordable.

Pure block-first with only a final stitch is not a supported route.
