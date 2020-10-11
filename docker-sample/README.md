# How to use docker to run this project in production

create folder structure like below:

## Create a project (can be any name) folder for all files

`/project/albireo/Albireo` // this is your git repo directory

`/project/config/albireo/config.yml` // this is the config file copied from /project/albireo/Albireo/config/config.sample.yml

`/project/config/albireo/sentry.yml` // this is optional. you may not need this

`/project/config/alembic.ini` // this is for upgrading database if you want to keep update with the official branch. copy a sample file from /project/albireo/Albireo/alembic.ini.example

`/project/config/deluge` // for deluge config file

`/project/data/downloads` // temp folder for deluge downloads locations.

## Create folders for video and other data files

Grant permission for you `docker` user group

`/docker_data/albireo/data`

`/docker_data/postgres`

## Copy Dockerfile and docker-compose.yml

Copy `Dockerfile` from docker-sample/ to `/project/albireo/`

Copy `docker-compose.yml` to `/project/docker-compose.yml`

## Update the fields in config

Update the fields in `/project/config/config.yml`

You must:
- update the `database` section with the correspondent value you set in the docker-compose.yml for postgres
- update the `app_secret_key`, `app_secret_password_salt` to any value you like for security reason.
- update the `site` section in order for the email activation to work
- update the `mail` section for flask-mail

Update the fields in `/project/config/alembic.ini`

You must:
- update the `sqlalchemy.url` to your database url

## Update the config for postgres and deluge

You need the docker image for postgres and deluge to see how to configure those image

## Start docker-compose

from the `/project` directory. run docker-compose up to start all service