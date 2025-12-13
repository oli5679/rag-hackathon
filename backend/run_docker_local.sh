#!/bin/bash
docker run --env-file .env -p 8080:8080 spareroom-api-test
