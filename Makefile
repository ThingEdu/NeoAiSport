.PHONY: install install-lean run run-mouse test lint

install:        ## cài đầy đủ (mediapipe kéo opencv-contrib)
	python -m venv .venv && .venv/bin/pip install -e ".[dev]"

install-lean:   ## cài gọn cho ARM/NEO: tránh trùng opencv (dùng headless)
	python -m venv .venv && .venv/bin/pip install -e . && \
	.venv/bin/pip install --no-deps mediapipe && \
	.venv/bin/pip install opencv-contrib-python-headless numpy absl-py flatbuffers sounddevice

run:            ## màn tổng — chọn game thị giác
	.venv/bin/python -m neoaisport.hub

run-batde:      ## Bắt Dế bằng camera
	.venv/bin/python -m neoaisport.batde.app --source camera

run-mouse:      ## Bắt Dế bằng chuột (không cần webcam)
	.venv/bin/python -m neoaisport.batde.app --source mouse

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check src tests
