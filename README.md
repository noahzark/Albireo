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

### vagrant
you can also set up the development environment with [Vagrant](https://www.vagrantup.com/)

the vagrant vm is based on Ubuntu 14.04

```bash
vagrant up
vagrant ssh
```

## Server

the server is a flask app which provide http API for management and end user page (planned but not added currently).


To start the server, run `python server.py`, if you set the environment variable DEBUG=True, the debug info will be print to log

### HTTP API

Admin API

root: /api/admin/

**all api need login and user level >= 2**

#### List bangumi in database
GET `/api/admin/bangumi?page=<page number>&count=<number per page>&sort_field=<sort field>&sort_order=<sort order>&name=<name>`

Params
- page: default 1, current page
- count default 10, number per page
- sort_field: default 'update_time', the field used to sort the result
- sort_order: default 'desc', the order used to sort the result, can 'asc' or 'desc'
- name: default None, to filter the result by name

Return:

status: 200
body:
```json
{
    "total": 2,
    "data": [
        {
            "status": 1,
            "bgm_id": 140001,
            "update_time": 1462176050499,
            "eps_regex": "【恶魔岛字幕组】\\*?从零开始的异世界生活\\*?[(\\d+)\\]\\[GB\\]\\[720P\\]\\[MP4\\]",
            "name": "Re:ゼロから始める異世界生活",
            "air_date": "2016-04-03",
            "image": "http://lain.bgm.tv/pic/cover/l/cb/78/140001_Ew1mo.jpg",
            "name_cn": "Re：从零开始异世界生活",
            "eps": 25,
            "summary": "　　从便利店回来的路上突然被召唤到异世界的少年，菜月昴。在无可依赖的异世界，无力的少年所唯一拥有的力量……那就是死后便会使时间倒转的“死亡回归”的力量。为了守护重要的人，并取回那些无可替代的时间，少年向绝望抗争，挺身面对残酷的命运。",
            "create_time": 1462176050499,
            "air_weekday": 7,
            "id": "85a21948-b2e5-43dc-93e9-3ad71f662bdf",
            "rss": "https://share.dmhy.org/topics/rss/rss.xml?keyword=%E5%BE%9E%E9%9B%B6+%E6%81%B6%E9%AD%94%E5%B2%9B+GB"
        },
        {
         ...
        }
    ]
}
```

#### Get a bangumi detail
GET `/api/admin/bangumi/:id`

Params:
- id the bangumi.id, note that this is not bgm_id

Return:

status: 200
body:
```json
{
    "data": {
        "status": 1,
        "bgm_id": 140001,
        "update_time": 1462613862631,
        "name": "Re:ゼロから始める異世界生活",
        "air_date": "2016-04-03",
        "image": "http://lain.bgm.tv/pic/cover/l/cb/78/140001_Ew1mo.jpg",
        "name_cn": "Re：从零开始异世界生活",
        "eps": 25,
        "summary": "　　从便利店回来的路上突然被召唤到异世界的少年，菜月昴。在无可依赖的异世界，无力的少年所唯一拥有的力量……那就是死后便会使时间倒转的“死亡回归”的力量。为了守护重要的人，并取回那些无可替代的时间，少年向绝望抗争，挺身面对残酷的命运。",
        "episodes": [
            {
                "status": 1,
                "episode_no": 1,
                "update_time": 1462176050495,
                "name": "始まりの終わりと終わりの始まり",
                "airdate": "2016-04-03",
                "bangumi_id": "85a21948-b2e5-43dc-93e9-3ad71f662bdf",
                "bgm_eps_id": 621357,
                "name_cn": "起始的终结和终结的起始",
                "create_time": 1462176050495,
                "duration": "00:49:30",
                "id": "d22659a3-9ed9-438d-9548-f573e26e72bc"
            },
            {
                ...
            }
        ],
        "eps_regex": "【恶魔岛字幕组】.*?从零开始的异世界生活.*?\\[(\\d+)\\]\\[GB\\]\\[720P\\]\\[MP4\\]",
        "create_time": 1462176050499,
        "air_weekday": 7,
        "id": "85a21948-b2e5-43dc-93e9-3ad71f662bdf",
        "rss": "https://share.dmhy.org/topics/rss/rss.xml?keyword=%E5%BE%9E%E9%9B%B6+%E6%81%B6%E9%AD%94%E5%B2%9B+GB"
    }
}
```

#### Add a bangumi
POST `/api/admin/bangumi`

Request Body:
```json
{
	"bgm_id": 144843,
	"name": "ハイスクール・フリート",
	"name_cn": "高校舰队",
	"summary": "「生于大海，守护大海，去往大海——那就是“蓝色人鱼”！」\r\n距今约100年前，由于板块运动，日本的大部分国土被水淹没而消失。\r\n为了保全国土而接连建成的水上都市不知何时成为了海上都市，随着连结它们的航路增大，需要更多的人员来保护海洋安全。\r\n由此，工作的女性进出海上、守护海洋安全的职业“蓝色人鱼”成为了女学生们憧憬的存在。\r\n在这样的时代，幼时好友的岬明乃和知名萌香，和拥有“成为蓝色人鱼”这一目标的伙伴们一起，进入了横须贺的海洋高中学习。",
	"image": "http://lain.bgm.tv/pic/cover/l/83/dd/144843_1nqUr.jpg",
	"air_date": "2016-04-09",
	"air_weekday": 6,
	"episodes": [{
		"bgm_eps_id": 617753,
		"episode_no": 1,
		"name": "初航海でピンチ！",
		"name_cn": "初次航海大危机！",
		"duration": "00:24:00",
		"airdate": "2016-04-09"
	}, {
	    ...
	}],
	"eps": 12
}
```

Return:
status: 200
```json
{
	"data": {
		"id": "18b8989c-e639-47d9-88eb-65444f1593c8"
	}
}
```

#### Update a bangumi
PUT `/api/admin/bangumi/:id`

Request Body:
```json
{
	"status": 1,
	"bgm_id": 144843,
	"update_time": 1462607307392,
	"eps_regex": "【极影字幕社】\\s*.*?\\s*高校舰队\\/青春波纹\\s*Haifuri\\s*第(\\d+)话\\s*GB\\s*720P\\s*MP4",
	"name": "ハイスクール・フリート",
	"air_date": "2016-04-09",
	"image": "http://lain.bgm.tv/pic/cover/l/83/dd/144843_1nqUr.jpg",
	"name_cn": "高校舰队",
	"eps": 12,
	"summary": "「生于大海，守护大海，去往大海——那就是“蓝色人鱼”！」\r\n距今约100年前，由于板块运动，日本的大部分国土被水淹没而消失。\r\n为了保全国土而接连建成的水上都市不知何时成为了海上都市，随着连结它们的航路增大，需要更多的人员来保护海洋安全。\r\n由此，工作的女性进出海上、守护海洋安全的职业“蓝色人鱼”成为了女学生们憧憬的存在。\r\n在这样的时代，幼时好友的岬明乃和知名萌香，和拥有“成为蓝色人鱼”这一目标的伙伴们一起，进入了横须贺的海洋高中学习。",
	"create_time": 1462607307392,
	"air_weekday": 6,
	"id": "18b8989c-e639-47d9-88eb-65444f1593c8",
	"rss": "https://share.dmhy.org/topics/rss/rss.xml?keyword=%E9%AB%98%E6%A0%A1%E8%88%B0%E9%98%9F+%E6%9E%81%E5%BD%B1+GB"
}
```

Return:
status: 200
```json
{
    "msg": "ok"
}
```

#### Delete a bangumi
DELETE `/api/admin/bangumi/:id`

Return:
```json
{
    "msg": "ok"
}
```

#### Search a bangumi
GET `/api/admin/query?name=<name>`

Params:
- name the name of the bangumi, this name will be used to search with bgm.tv search api

Return:
status: 200
```json
{
	"data": [{
		"bgm_id": 144843,
		"rating": {
			"count": {
				"10": 0,
				"1": 0,
				"3": 0,
				"2": 0,
				"5": 0,
				"4": 0,
				"7": 0,
				"6": 0,
				"9": 0,
				"8": 0
			},
			"total": 0,
			"score": 0
		},
		"name": "\u30cf\u30a4\u30b9\u30af\u30fc\u30eb\u30fb\u30d5\u30ea\u30fc\u30c8",
		"air_date": "",
		"image": "http://lain.bgm.tv/pic/cover/l/83/dd/144843_1nqUr.jpg",
		"name_cn": "\u9ad8\u6821\u8230\u961f",
		"eps": 0,
		"rank": 0,
		"summary": "",
		"air_weekday": 0,
		"id": "18b8989c-e639-47d9-88eb-65444f1593c8"
	}]
}
```

the return json format is almost the same with bgm.tv search api, but convert the id to bgm_id, and if id is existed, that means this bangumi is already added to database

#### Search a bangumi detail
GET `/api/admin/query/:bgm_id`

Params:
- bgm_id the bangumi.tv id

Return:
totally same with bangumi.tv search api. see https://github.com/jabbany/dhufufu/blob/master/bangumi/api.txt#L176


#### update an episode
GET `/api/admin/bangumi/<bangumi_id>/episode/<episode_id>`

Params:
- bangumi_id the bangumi id of the episode
- episode_id, episode id

request body
```json
{
    "status": 1,
    "episode_no": 1,
    "update_time": 1462176050495,
    "name": "始まりの終わりと終わりの始まり",
    "airdate": "2016-04-03",
    "bangumi_id": "85a21948-b2e5-43dc-93e9-3ad71f662bdf",
    "bgm_eps_id": 621357,
    "name_cn": "起始的终结和终结的起始",
    "create_time": 1462176050495,
    "duration": "00:49:30",
    "id": "d22659a3-9ed9-438d-9548-f573e26e72bc"
},
```

**Note that only `name`, `name_cn`, `duration`, `airdate` will be updated**

Returns
```json
{
    'msg': 'ok'
}
```

### Scheduler

Scheduler is the core of this project ,it work like an cron daemon and periodically visit the bangumi rss to see if there are episode need to be downloaded.

To run Scheduler, run `python scheduler.py` is enough, if you set environment variable DEBUG to True, debug info will be printed.
