#Generic single-database configuration.

##Migration guide:

Before run alembic, add current working directory to environment

```
export PYTHONPATH=`pwd`
```

Setup your config file, this file is the `alembic.ini` should located in your project root folder. you just copy the alembic.ini.example and rename it to alembic.ini.

edit alembic.ini, update sqlalchemy.url to your database config.

If you are first time download this project, You don't need run update script. If you have deployed this project ever before. You need to run the update script to auto update databases

First make sure you have alembic installed, then run the following command:

```
$ alembic upgrade head
```

alembic will update database for you.
