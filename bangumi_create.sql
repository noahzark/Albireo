-- Created by Vertabelo (http://vertabelo.com)
-- Last modification date: 2016-02-28 14:39:12.924




-- tables
-- Table: bangumi
CREATE TABLE bangumi (
    id uuid  NOT NULL,
    bgm_id int  NOT NULL,
    name text  NOT NULL,
    name_cn text  NOT NULL,
    eps int  NOT NULL DEFAULT 0,
    summary text  NOT NULL,
    image text  NOT NULL,
    air_date date  NOT NULL,
    air_weekday int  NOT NULL,
    rss text  NULL,
    eps_regex text  NULL,
    status int  NOT NULL,
    create_time timestamp  NOT NULL,
    update_time timestamp  NOT NULL,
    CONSTRAINT bangumi_pk PRIMARY KEY (id)
);



-- Table: episodes
CREATE TABLE episodes (
    id uuid  NOT NULL,
    bangumi_id uuid  NOT NULL,
    bgm_eps_id int  NOT NULL,
    episode_no int  NOT NULL,
    name text  NULL,
    name_cn text  NULL,
    duration VARCHAR(256) NULL,
    airdate date  NULL,
    status int  NOT NULL,
    torrent_id VARCHAR(256)  NULL,
    create_time timestamp  NOT NULL,
    update_time timestamp  NOT NULL,
    CONSTRAINT episodes_pk PRIMARY KEY (id)
);



-- Table: torrentfile
CREATE TABLE torrentfile (
    id uuid  NOT NULL,
    episode_id uuid NOT NULL,
    torrent_id VARCHAR(256) NOT NULL,
    file_path TEXT NULL,
    CONSTRAINT torrentfile_pk PRIMARY  KEY (id)
);





-- foreign keys
-- Reference:  episodes_bangumi (table: episodes)

ALTER TABLE episodes ADD CONSTRAINT episodes_bangumi 
    FOREIGN KEY (bangumi_id)
    REFERENCES bangumi (id)
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE 
;



-- foreign keys
-- Reference: torrentfile_episodes (table: torrentfile)

ALTER TABLE torrentfile ADD CONSTRAINT torrentfile_episodes
    FOREIGN KEY (episode_id)
    REFERENCES episodes (id)
    NOT DEFERRABLE
    INITIALLY IMMEDIATE
;



-- End of file.

