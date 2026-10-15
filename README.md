# CAD Ingestion Harness

A Python prototype for parsing, validating, and translating vendor-style CAD component data into a normalized representation.

The project explores core engineering challenges in CAD file I/O: handling variations in external schemas, validating component data, rejecting malformed boards, and testing parser behavior across a collection of input fixtures.

## Project Goals

- Parse vendor-style JSON exports containing board component data.
- Normalize supported variations in component field names into a consistent representation.
- Validate component records using Pydantic.
- Reject an entire board when a component is malformed, rather than returning a partially parsed board.
- Generate synthetic input fixtures to exercise supported schema variations and malformed-data scenarios.
- Evaluate parser behavior across a batch of input files.
- Provide a foundation for future experiments in AI-assisted schema mapping and evaluation.

## Current Scope

This is a learning and portfolio project using synthetic, vendor-style JSON data. It is not an implementation of any proprietary CAD file format, and it does not currently integrate with actual PCB design tools.

The current normalized component model contains:

- `component_id`
- `component_type`
- `x_position`
- `y_position`

This simplified representation provides a starting point for exploring how external data can be mapped into a consistent internal schema.

## Architecture

### Parser — `src/parser.py`

Reads a vendor-style JSON file, extracts its component records, normalizes supported field-name variations, and validates each component using Pydantic.

The parser currently recognizes `comp_id` or `id` as the component identifier, and `type` or `part_type` as the component type. Missing required identifiers or coordinates, invalid data types, and malformed component structures cause parsing to fail.

The parser follows a strict whole-board validation policy: if any component is malformed, the board is rejected.

### Generator — `src/generator.py`

Converts normalized component records back into a vendor-style JSON structure, including a header, board metadata, and component records.

This provides a starting point for testing data translation in both directions.

### Fixture Generator — `scripts/generate_fixtures.py`

Generates synthetic JSON exports with variations in field names and deliberately malformed component data.

The generator uses randomized choices, so generated datasets can vary between runs.

### Evaluation Harness — `src/evaluate.py`

Processes JSON fixtures in a directory and reports the number of files successfully parsed and the number rejected or otherwise failed.

The current evaluator measures parsing outcomes. It does not yet compare normalized output against a complete set of expected component values, so a successful parse does not independently establish semantic correctness.

### Tests — `tests/`

Contains unit tests for parser behavior, generator behavior, and batch evaluation, including valid inputs and several failure scenarios.

## Requirements

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Setup

Clone the repository and check out the branch you want to work on.

```bash
git clone https://github.com/Munnu/cad-ingest-harness.git
cd cad-ingest-harness
git switch develop
```

Create the project environment and install the locked dependencies:

```bash
uv sync
```

## Running the Project

### Parse the sample export

```bash
uv run python -m src.parser
```

### Generate synthetic fixtures

```bash
uv run python scripts/generate_fixtures.py
```

By default, fixtures are written to `data/json/`.

### Evaluate a batch of fixtures

Generate the fixtures first, then run:

```bash
uv run python -m src.evaluate
```

The evaluator reports how many files were processed, successfully parsed, and rejected or failed.

### Run the unit tests

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

### Run the linter

```bash
uv run ruff check .
```

## Validation Policy

A board is accepted only if all of its component records pass the parser's validation requirements.

If a component is malformed or missing required data, parsing fails for the entire board. This policy avoids silently returning an incomplete board representation.

## Current Limitations

- Input data is synthetic JSON rather than actual proprietary CAD exports.
- The normalized model represents only a small subset of the information found in a PCB design.
- Only explicitly supported field-name variations are normalized.
- Fixture generation is randomized and is not yet a fully reproducible benchmark.
- The evaluator reports parsing outcomes but does not yet measure exact normalized-output correctness.
- AI-assisted schema mapping and model evaluation are planned experiments, not implemented features.

## Potential Next Steps

1. Add fixed fixtures with explicit expected outcomes.
2. Extend evaluation to compare parsed component values against expected normalized records.
3. Make supported and unsupported schema variations explicit.
4. Experiment with AI-assisted schema mapping and evaluate proposed mappings against known results.
5. Expand the normalized model and validation rules as the project's scope develops.

## License

No license has been specified yet.
