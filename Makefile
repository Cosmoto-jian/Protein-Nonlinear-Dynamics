PY ?= python3
.PHONY: next gates status all all-cheap all-force figures-fast validate validate-full paper
next:
	$(PY) tools/next.py
gates:
	$(PY) tools/gates.py
status:
	$(PY) run_all.py --status
all:
	$(PY) run_all.py
all-cheap:
	$(PY) run_all.py --cheap
all-force:
	$(PY) run_all.py --all
figures-fast:
	$(PY) run_all.py --fast
validate:
	$(PY) tools/validate.py
validate-full:
	$(PY) tools/validate.py --full
paper:
	cd writing/tex && latexmk -pdf main.tex
