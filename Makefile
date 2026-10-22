PY ?= python3
.PHONY: gates figures figures-fast all graph paper validate validate-full
gates:
	$(PY) tools/gates/run_all.py
figures figures-fast:
	$(PY) run_all.py --fast
all:
	$(PY) run_all.py --full
graph:
	$(PY) tools/graph.py
paper:
	cd writing/tex && latexmk -pdf main.tex
validate:
	$(PY) tools/validate.py
validate-full:
	$(PY) tools/validate.py --full
