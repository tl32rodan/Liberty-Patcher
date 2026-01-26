PYTHON ?= python

.PHONY: test demo_patch demo_format clean

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

demo_patch:
	$(PYTHON) demo_patch.py

demo_format:
	$(PYTHON) demo_format.py

clean:
	rm -f formatted_output.lib patched_output.lib
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
