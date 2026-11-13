# 20261113T080049.458484Z-I3-CPU-tooling-ec07b3054b

Sample: `watershed-qualification-include-search-path-failure`

Outcome: **VALIDATOR_GAP**

Qualification include scanner omits actual compiler -I rocm/common/image; original entry includes watershed_sample.hpp. GPU implementation and existing numeric proofs unchanged. rc=1
