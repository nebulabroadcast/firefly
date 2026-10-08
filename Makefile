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

build: check_version skin
	poetry run pyinstaller -y firefly.windows.spec
	cp -r images dist/images
	cp -r skin.css dist/skin.css
	cp -r fonts dist/fonts
	
build_windows: build
	# make zip
	cd dist && zip -r ../firefly-$(VERSION)-win.zip firefly.exe images fonts skin.css

build_linux: build
	# make tar
	cd dist && tar -czvf ../firefly-$(VERSION)-linux.tar.gz firefly images fonts skin.css
