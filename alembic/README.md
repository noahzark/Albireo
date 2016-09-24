#Generic single-database configuration.

##Migration guide:

Before run alembic, add current working directory to environment

```
export PYTHONPATH=`pwd`
```


If you are first time download this project, You don't need run update script. If you have deployed this project ever before. You need to run the update script to auto update databases

First make sure you have alembic installed, then run the following command:

```
$ alembic upgrade head
```

alembic will update database for you.
