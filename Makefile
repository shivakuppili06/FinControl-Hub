.PHONY: setup test run run-dashboard

setup:
	pip install -r requirements.txt

test:
	pytest tests/

run:
	python run_pipeline.py

run-dashboard:
	streamlit run app.py
