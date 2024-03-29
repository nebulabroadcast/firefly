.PHONY=skin
VERSION=$(shell poetry run python -c 'import firefly; print(firefly.__version__)')

run: skin
	poetry run python -m firefly

skin:
	poetry run qtsass -o skin.css skin.scss

check_version:
	sed -i "s/version = \".*\"/version = \"$(VERSION)\"/" pyproject.toml

lint: check_version
	poetry run isort firefly
	poetry run black firefly
	poetry run flake8 firefly
	poetry run mypy firefly

build: check_version skin
	poetry run pyinstaller -y firefly.windows.spec
	cp -r images dist/images
	cp -r skin.css dist/skin.css
	
build_windows: build
	# make zip
	cd dist && zip -r ../firefly-$(VERSION)-win.zip firefly.exe images skin.css

build_linux: build
	# make tar
	cd dist && tar -czvf ../firefly-$(VERSION)-linux.tar.gz firefly images skin.css
