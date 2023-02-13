.PHONY=skin

run: skin
	poetry run python -m firefly

install:
	cp firefly.desktop ~/.local/share/applications/firefly.desktop
	echo 'Path=$(CURDIR)' >> ~/.local/share/applications/firefly.desktop
	echo 'Icon=$(CURDIR)/images/icon.png' >> ~/.local/share/applications/firefly.desktop

skin:
	poetry run qtsass -o skin.css skin.scss
