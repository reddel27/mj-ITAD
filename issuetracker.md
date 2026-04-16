# MJ-ITAD Issue Tracker Checklist

- [x] P0 | Homepage does not render the dispensary browser | labels: bug, frontend, p0
- [x] P0 | Prevent backend startup crash when Google Maps API key is missing | labels: bug, backend, config, p0
- [x] P1 | Remove silent mock dispensary fallback in production | labels: bug, backend, reliability, p1
- [x] P1 | Stop mutating the database in GET /products | labels: bug, backend, api, p1
- [ ] P1 | Add stable deduplication rules for dispensaries | labels: enhancement, backend, data-quality, p1 | status: code updated, migration/table-update plan pending
- [x] P1 | Add explicit request and response schemas | labels: enhancement, backend, api, p1
- [x] P1 | Make CORS origins environment-driven | labels: bug, backend, security, config, p1
- [x] P2 | Clean up setup docs (duplicate section and Docker link usage) | labels: documentation, devops, p2
- [x] P2 | Remove reload mode from default backend container command | labels: devops, backend, p2
- [x] P2 | Wire or remove unused standalone map component | labels: tech-debt, frontend, p2
- [ ] P2 | Add automated tests for critical backend flows | labels: testing, backend, p2 | status: `python3 -m pytest -q` passes (3 tests), missing key/upstream failure-path tests and CI integration still pending
- [ ] P3 | Implement menu scraping and normalized product ingestion pipeline | labels: enhancement, backend, data-ingestion, roadmap, p3
