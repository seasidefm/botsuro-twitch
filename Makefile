SHELL = /bin/bash
run:
	. .env
	./venv/bin/python main.py
prepare:
	docker run --rm --privileged linuxkit/binfmt:v0.8

build: prepare
	docker buildx build --platform linux/arm64 --load -t registry.dougflynn.dev/botsuro -f docker/Dockerfile .

deploy:
	docker build -t redbirddigital/botsuro -f docker/Dockerfile .
	docker push redbirddigital/botsuro
# 	docker buildx build --platform linux/arm64,linux/amd64 --push -t registry.dougflynn.dev/botsuro-api -f docker/Dockerfile.server .
	sleep 10
	kubectl rollout restart -n seasidefm deployment botsuro-twitch
