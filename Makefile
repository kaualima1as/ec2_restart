.PHONY: install
install:
	curl -Ls https://astral.sh/uv/install.sh | sh
	uv venv --python=python3.11
	uv pip install .
	.venv/bin/pre-commit install

.PHONY: push
push:
	git add .
	git commit -m "feat: Update"
	git push -u origin main
