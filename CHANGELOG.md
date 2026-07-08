# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- `migration-factory` CLI with `assess`, `plan-waves`, `status`, and `report`
  subcommands that read and write JSON inventory files.
- Assessment engine computing 6 Rs disposition recommendations and a 0-100
  readiness score.
- Wave planner that groups servers into dependency-ordered waves within a
  configurable maximum wave size.
- Migration orchestrator enforcing the
  `pending -> replicating -> testing -> cutover -> complete` state machine.
- Pydantic domain models for Server, Application, Wave, and MigrationTask.
- Terraform deployment infrastructure (S3 artifact bucket, DynamoDB state
  table, IAM role) with a reusable `state-store` module and dev/prod
  environments.
- Documentation, CI pipeline, pre-commit hooks, and open-source project files.
