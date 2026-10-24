.PHONY: quality validate

quality:
	python3 tools/validate/hygiene.py

validate:
	bash run-validation.sh
