# MetroPy
Project for CSCI 6511 Artificial Intelligence -- the idea  is to use the A* algorithm to implement efficient routing through the DC Metro which can account for current train locations, station outages, or line closings. Currently finds the best path based on distances, but line delays and station outages can be manually simulated and the algorithm adjusts accordingly. Future plans will dynamically account for this by parsing Metro delays and warnings.

For detailed information and test results, see Report.pdf.

# Requirements
Requires `python3` and the `requests` Python library.
