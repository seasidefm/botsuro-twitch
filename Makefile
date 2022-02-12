prepare:
	docker run --rm --privileged linuxkit/binfmt:v0.8

build: prepare
	docker buildx build --platform linux/arm64 --load -t registry.dougflynn.dev/botsuro -f docker/Dockerfile .

deploy:
	docker buildx build --platform linux/arm64 --push -t registry.dougflynn.dev/botsuro -f docker/Dockerfile .
# 	docker buildx build --platform linux/arm64,linux/amd64 --push -t registry.dougflynn.dev/botsuro-api -f docker/Dockerfile.server .
	sleep 8
	kubectl rollout restart -n botsuro deployment botsuro-deployment