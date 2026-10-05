# Examples

retrofit.ttl is synthetic. Two dated GMOnt records describe the same zone and document
two RCOnt versions with separate model snapshots. Resistance changes from 0.0075 to
0.0120 K/W; capacitance remains 15,000,000 J/K. These are illustrative values, not MEEB
measurements. Reserved example.org media URLs are not downloaded.

The filtered three-hop path from AfterRecord to RAfter follows documentsModelVersion,
hasModelSnapshot and hasResistance. Unfiltered traversal can find a shorter path via
the shared zone; use a predicate filter when a particular relationship is required.
