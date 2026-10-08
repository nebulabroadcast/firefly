.PHONY=skin
VERSION=$(shell uv run python -c 'import firefly; print(firefly.__version__)')

run: skin
	uv run python -m firefly

skin:
	uv run qtsass -o skin.css skin.scss

check_version:
	uv version $(VERSION)

lint: check_version
	uv run ruff check . --select=I --fix
	uv run ruff format .
	uv run ruff check . --fix
	uv run mypy .

# skin.css, images and fonts are read from the working directory at runtime,
# so they ship next to the binary
build: check_version skin
	uv run pyinstaller -y firefly.spec
	cp -r images fonts skin.css dist/

build_windows: build
	cd dist && zip -r ../firefly-$(VERSION)-win.zip firefly.exe images fonts skin.css

build_linux: build
	cd dist && tar -czvf ../firefly-$(VERSION)-linux.tar.gz firefly images fonts skin.css
