# Beacon nodes

This option accepts a comma separated list of beacon nodes which will be used to fetch the necessary duty data.

The list should be in the following format:

* `--beacon-nodes http://localhost:5052,http://localhost:5051,...`

The first beacon node in the provided list which is ready to accept requests is used for every API call as long as it stays ready. If this changes the next ready node will be used and so on and so forth.
