#0.8.0-alpha

##Database changes:

Add a new table 'server_session' for persist session on database. may fix the occasionally 401 issues.
TO UPDATE TABLE, read the [update document](https://github.com/lordfriend/Albireo/blob/master/alembic/README.md).

##Bug fix

- fix the always empty issues when add new bangumi caused by bgm.tv anti-bot mechanism
- 

#0.7.0-alpha

##Database changes:

Add a new table `feed` is added for the new scheduler, besides, rss, regex in `bangumi` table is no longer used. Two columns `dmhy` and `acg_rip` are added to `bangumi` table.

TO UPDATE TABLE, read the [update document](https://github.com/lordfriend/Albireo/blob/master/alembic/README.md).

#NEW API:

Add two api for add dmhy and acg.rip keywords.

#New Scheduler

The new scheduler will individual task for each site, each task takes the feed periodically and save its find into feed table. A scanner will scan the feed table every 30 seconds.


#0.6.0-alpha

##Features Add

- InfoScanner for scanning missing information (name, name_cn, duration) and auto fill those information from bangumi.tv, note that the name_cn is not always filled.

##Bug fix

- rollback session when db connection lost

NOTE: this release require use to update their config.yml.

#0.4.0-alpha

##Features Add

- Add a CLI command to download bangumi cover image

##Breaking Changes

- Now, all client bangumi image will use bangumi.cover to get the cover image. if your see a broken image, using `tools.py --cover` to download missing bangumi cover.


#0.3.0-alpha

##Features Add

- New API:
    - on_air which list all bangumi currently on air,
    - bangumi_detail which get an bangumi detail, this api is the same api of admin bangumi detail but without admin permission
    - list_bangumi which is almost the same with admin api list bangumi

- Docker support


##Other changes

- default auto generated thumbnail is set to 00:00:01.000 frame


#0.2.0-alpha

##Features Add

- Home api for end user
- Episodes api for managing episodes
- Alembic SQLAlchemy migrate tool for migrate database
- Vagrant support for a quickly deployment with Vagrant
- Episode thumbnail generation
- Bangumi cover now will downloaded to local server

##Breaking Changes
- get bangumi api now return all episodes of this bangumi. access it with `episodes` field
- init db using sql script is not recommended, using tools.py to init db.
- ffmpeg is now a dependency to generate thumbnail for episode
- server.py now only used in development, when deploying in production, use `twistd -n web --port 5000 --wsgi appd.app`
