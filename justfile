[private]
default:
	@just --list

# setup virtual environment
devel:
	@uv sync --frozen --group sqlite --group postgres

# tidy everything with ruff
tidy:
	@uv run --frozen ruff check --fix

# run the test suite
test:
	@uv run --frozen pytest

# run the typechecker
typecheck:
	@uv run --frozen mypy src

# clean up any caches or temporary files and directories
clean:
	@rm -rf .mypy_cache .pytest_cache .ruff_cache .venv dist htmlcov .coverage tests/results.xml .coverage.*
	@find . -name \*.orig -delete

# install tools (you'll have to ensure you have uv already installed)
tools:
	@uv tool install ruff

# serve the documentation locally
[group('documentation')]
serve-docs: docs
	python3 -m http.server -d site

# build the documentation site
[group('documentation')]
docs:
	rm -rf site
	cd docs && pandoc index.md \
		--standalone \
		--from markdown+link_attributes \
		--to chunkedhtml \
		--variable toc \
		--toc-depth 2 \
		--chunk-template "%i.html" \
		--template template.html \
		--highlight-style solarizeddark.theme \
		--output "../site"

# regenerate the sri hashes
sri:
	@uv run --frozen python -m descant.sri
