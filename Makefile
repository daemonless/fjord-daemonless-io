# fjord.daemonless.io

ZENSICAL = zensical
# Zensical opens many files via pygments; raise the fd limit where allowed.
ZEN_ULIMIT = ulimit -n $$(ulimit -Hn) 2>/dev/null || true;

.PHONY: build serve clean

build:
	@echo "==> Building site with Zensical..."
	$(ZEN_ULIMIT) $(ZENSICAL) build -f zensical.toml

serve: build
	@echo "==> Serving site/ at http://0.0.0.0:8002"
	python3 -m http.server -d site --bind 0.0.0.0 8002

clean:
	rm -rf site/
