.PHONY: release-version

release-version:
	python3 scripts/release_version.py $(or $(BUMP),patch)
	uv lock
