# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## unreleased

### Changed

- Require input for Mosaik Setup: Database name

## 0.2.0

released: 2022-12-08

### Added

- support for Mosaik (Microsoft SQL Server)

## 0.1.0

released: 2022-12-05

### Inital release

- Configure behaviour based on config file.
- Connect to the wattro REST sync api.
- read data from a source system.
    - supported: Benning (SQLite) and TopKontor (Advantage DB)
- create new entities.
- update changed entities.
- log to file.
- send different log levels via mail.