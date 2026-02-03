DB_FILE_PATH ?= $(HOME)/.mvave_drumbrute.db

setup:
	uv sync

run:
	uv run python mvave_drumbrute.py \
	--db-file-path=$(DB_FILE_PATH)

run-quiet:
	uv run python mvave_drumbrute.py \
	--quiet \
	--db-file-path=$(DB_FILE_PATH)
