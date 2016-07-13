# Albireo
A bangumi auto download and management project
This is the backend part.
The web client for this project is [Deneb](https://github.com/lordfriend/Deneb)

## Motivation

There are an existed resolution for auto download bangumi from dmhy or other bt site by using flexget to parse the rss feed periodically. but that resolution is hard to manage the downloaded
file when the number of bangumi is growing. So I write this project to make the same way to auto download bangumi but associate the downloaded file with information provided by bangumi.tv.
further more, the information can be used for more user friendly function.

[Installation](#installation)

[Server](#server)

[Nginx Configuration](#nginx-configuration)

[Scheduler](#scheduler)

## Installation

requirements: python 2.7, deluge, postgresql 9.3 and above, ffmpeg

### dependencies:

- SQLAlchemy 1.0
- psycopg2
- flask 0.10
- flask-login 0.0.3
- PyYAML
- Twisted
- feedparser
- httplib2
- service_identity
- requests

NOTE: ffmpeg is presume accessible with `ffmpeg` command

### config file

Setup your config file by copying the `config/config-sample.yml` to `config/config.yml`, then modify the database and deluge config on demand

There are some config that must be modified before your run the project

- download
    - location this is the default location of downloaded file, you should set this **absolute path** to your own download directory which your application and deluge has the permission to write

- app_secret_key this is used by flask to encrypt session for security reason

### init database

using tools.py in the root directory of this project to init db

```bash
$ python tools.py --db-init # create tables if not exists

$ python tools.py --user-add admin 1234  # admin is username 1234 is password

$ python tools.py --user-promote admin 3  # admin is username 3 is the level, currently means super user
```

### set your server locale

To avoid some unicode issues, it is recommended to set locale of your server

### Docker
you can also set up the development environment with [Docker](https://www.docker.com/)

Make sure you have copied config.yml

```bash
docker build .
docker run --rm -it -v "`pwd`:/albireo" -p 127.0.0.1:5000:5000 albireo
```

## Server

the server is a flask app which provide http API for management and end user page (currently not completed).

In development mode, using flask built-in server:

run `python server.py`, if you set the environment variable DEBUG=True, the debug info will be print to log

In production mode, using twistd as WSGI container

```shell
twistd -n web --port 5000 --wsgi appd.app
```

## Nginx Configuration

To serve the static files like images and videos, you need to setup a static file server, we recommend using nginx.
Here are nginx configurations.

**You need to serve the following url pattern.**

- bangumi cover: `{http|https}://{youdomain}/pic/{bangumi_id}/cover.jpg`
- episode thumbnail: `{http|https}://{youdomain}/pic/{bangumi_id}/thumbnails/{episode_no}.png`
- video: `{http|https}://{youdomain}/video/{bangumi_id}/{path_to_video}`

**explanation**
- yourdomain is the configured domain in `config/config.yml` file `domain` section
- bangumi_id is the bangumi id which is a uuid string
- episode_no is the episode number for certain episode
- path_to video is video file path relative to download path which configured in your config file.

In fact, you just need to take the path part after `/pic/` and append to your download location. the actual file is there.

For example your download path is `/path/to/videos` which is set in `config/config.yml` download location section

```nginx
server {
	listen 8000 default_server;
	
	root /path/to/videos;
	
	server_name localhost;
	
	location ~ ^(?:/pic|/video)/(.+) {
		try_files /$1 $uri=404;
	}
}
```

According to your environment and configuration, the nginx configuration may different from this example.


### Scheduler

Scheduler is the core of this project ,it work like an cron daemon and periodically visit the bangumi rss to see if there are episode need to be downloaded.

To run Scheduler, run `python scheduler.py` is enough, if you set environment variable DEBUG to True, debug info will be printed.

#### Rule of episode match

The scheduler will automatic parse the feed item of your rss url, it use a regular expression which you provide to match the certain episode number.

your regular expression must contain capture group that captures number of episode.

For example, an item in feed is

```xml
<item>
	<title>
	<![CDATA[
	【恶魔岛字幕组】★4月新番【Re：从零开始的异世界生活_Re - Zero Kara Hajimeru Isekai Seikatsu】[15][GB][720P][MP4][内附公告]
	]]>
	</title>
	<pubDate>Mon, 11 Jul 2016 07:51:04 +0800</pubDate>
	<enclosure url="magnet:?xt=urn:btih:57LCYNNOJDWR7A6K5DK6CDTNKXNUUCHV&dn=&tr=http%3A%2F%2F208.67.16.113%3A8000%2Fannounce&tr=udp%3A%2F%2F208.67.16.113%3A8000%2Fannounce&tr=http%3A%2F%2Ftracker.openbittorrent.com%3A80%2Fannounce&tr=http%3A%2F%2Ftracker.publicbt.com%3A80%2Fannounce&tr=http%3A%2F%2Ftracker.prq.to%2Fannounce&tr=http%3A%2F%2Fopen.acgtracker.com%3A1096%2Fannounce&tr=http%3A%2F%2Ftr.bangumi.moe%3A6969%2Fannounce&tr=https%3A%2F%2Ft-115.rhcloud.com%2Fonly_for_ylbud&tr=http%3A%2F%2Fbtfile.sdo.com%3A6961%2Fannounce&tr=http%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=https%3A%2F%2Ftr.bangumi.moe%3A9696%2Fannounce&tr=http%3A%2F%2Fopen.nyaatorrents.info%3A6544%2Fannounce&tr=http%3A%2F%2Ftracker.ktxp.com%3A6868%2Fannounce&tr=http%3A%2F%2Ftracker.ktxp.com%3A7070%2Fannounce&tr=http%3A%2F%2Ft2.popgo.org%3A7456%2Fannonce&tr=http%3A%2F%2Ftracker.openbittorrent.com%2Fannounce&tr=http%3A%2F%2Ftracker.publicbt.com%2Fannounce&tr=http%3A%2F%2Fshare.camoe.cn%3A8080%2Fannounce&tr=http%3A%2F%2Ftracker.dmhy.org%3A8000%2Fannounce&tr=http%3A%2F%2Fnyaatorrents.info%3A7266%2Fannounce&tr=http%3A%2F%2Ft.acg.rip%3A6699%2Fannounce" length="1" type="application/x-bittorrent"/>
</item>
```

Your regular expression can be `.+?从零开始的异世界生活.*?\[(\d+)\].+`

This regular expression will capture number `15` in the title `【恶魔岛字幕组】★4月新番【Re：从零开始的异世界生活_Re - Zero Kara Hajimeru Isekai Seikatsu】[15][GB][720P][MP4][内附公告]` of this item.

It is recommended test your regular expression before saved, you can use a web tool to test your regular expression. like http://regex101.com/#python
