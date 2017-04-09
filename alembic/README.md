#Generic single-database configuration.

##Migration Guide:

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


##Developer Guide:
When you add a new column, new table, you need to generate a alembic migration script for user to update from certain version to your modified version.

Usually, you just need run an auto-generate command after you have modified domain module.

```
alembic revision --autogenerate -m 'some comment'
```

for example, we add a column `bangumi_moe` to `bangumi` table.

- First, we add a field in Bangumi.py
- then we run alembic command: `alembic revision --autogenerate -m 'add column bangumi_moe to bangumi table'`.

We will see the following information.
 
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added column 'bangumi.bangumi_moe'
```

At last, run `alembic upgrade head` to make the change into your database.

**You must run auto generate before your have changed your database**

For more inforamation, see Alembic document [http://alembic.zzzcomputing.com/en/latest/autogenerate.html](http://alembic.zzzcomputing.com/en/latest/autogenerate.html)