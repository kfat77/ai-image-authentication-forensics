# P6-C Validation Coverage Matrix

| Population | Required scenario | Required metadata / slices |
|---|---|---|
| Real | camera photo | source, licence, camera/capture notes when lawfully available, original and distributed variants |
| Real | smartphone photo | device/computational-processing note where lawfully available, source-disjoint parent group |
| Real | news image | licensed newsroom/archive source, editorial transformation note |
| Real | online distributed image | permitted platform/distribution record and parent reference if available |
| AI | diffusion generated | documented method, source, resolution class, generation/collection limitation |
| AI | commercial generator | documented commercial-tool provenance where permission allows, source and quality slice |
| Transformation | JPEG compression | parent group, codec/quality description, transformed file hash |
| Transformation | screenshot | repeatable capture procedure, original/parent reference where available |
| Transformation | crop / resize | parent group and exact operation parameters |
| Transformation | editing | permitted edit provenance and transformation description |

Coverage is reported independently for every row. A gap remains a gap; it is not filled by relabeling an unverified source or reusing a parent image across splits.
