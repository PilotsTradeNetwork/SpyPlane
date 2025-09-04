#!/usr/bin/env bash
docker build . -t asia.gcr.io/pilotstradenetwork/spyplane:latest
docker push asia.gcr.io/pilotstradenetwork/spyplane:latest
