# Hydra
A scalable, fault-resistant distributed algotrading system written in Python3

## Component types:
- Manager: coordinates the other components, handles routing of signals
- Strategy: Consumes data, can be used both as an algotrading algo and as more of a research tool to analyze data (will probably be renamed at some point)
- Market Interface: Handles communication with exchanges or other external data sources, provides data feeds to requesting strategies and sends orders

## Planned improvements
- Introduce general-purpose worker pools to dynamically scale the system in response to increased load
- Non-volatile storage integrated into market interfaces
- Backfilling logic
- Implement orders from strategies
- Better handling of component discovery: right now if manager crashes no component knows where others are
