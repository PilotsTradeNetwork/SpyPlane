#!/usr/bin/env bash

docker build . -t asia.gcr.io/pilotstradenetwork/spyplane:latest

docker stop spyplane_flight || true && docker rm spyplane_flight || true

# If you face permissions during pull in gcloud VM, just run `docker-credential-gcr configure-docker`

cat .env

docker run \
       -it \
        -v ./workspace:/app/workspace \
        --env-file .env \
        --name spyplane_flight \
        --restart unless-stopped \
        asia.gcr.io/pilotstradenetwork/spyplane:latest

echo 'Spyplane deployment done!'
docker logs -f spyplane_flight
