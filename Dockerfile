FROM ubuntu:14.04

# comment this section out if you live outside firewall
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty main restricted" > /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty main restricted" >> /etc/apt/sources.list
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe" >> /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted" >> /etc/apt/sources.list
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty universe" >> /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty universe" >> /etc/apt/sources.list
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty multiverse" >> /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty multiverse" >> /etc/apt/sources.list
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-updates multiverse" >> /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-updates multiverse" >> /etc/apt/sources.list
RUN sudo echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
RUN sudo echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
# end F@ck GFW section

RUN sudo echo "deb http://ppa.launchpad.net/kirillshkrogalev/ffmpeg-next/ubuntu trusty main" >> /etc/apt/sources.list

RUN echo "Updating dependencies..."
RUN apt-get update

RUN echo "Installing deluge, postgresql, etc.."
RUN apt-get
# avoide invoke-rc.d: policy-rc.d denied execution of start
RUN echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d
RUN sudo apt-get -y --force-yes install deluged deluge-webui postgresql postgresql-contrib python-pip postgresql-client python-dev libyaml-dev python-psycopg2 ffmpeg

RUN echo "Setting up postgresql user and database..."
# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.3/main/pg_hba.conf

# And add ``listen_addresses`` to ``/etc/postgresql/9.3/main/postgresql.conf``
RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf

# Expose the PostgreSQL port
EXPOSE 5432
# http://askubuntu.com/questions/371832/how-can-run-sudo-commands-inside-another-user-or-grant-a-user-the-same-privileg
RUN usermod -a -G sudo postgres
USER postgres
RUN /etc/init.d/postgresql start && psql -U postgres -d postgres -c "alter user postgres with password '123456';"
RUN /etc/init.d/postgresql start && createdb -O postgres albireo


USER root
RUN useradd -p albireo -m albireo

USER albireo
WORKDIR /home/albireo
#"Setting up deluge user..."
RUN mkdir .config
RUN mkdir .config/deluge
RUN touch .config/deluge/auth
RUN echo ":deluge:10" >> ~/.config/deluge/auth

ADD . /home/albireo/

#"Installing python dependencies..."
USER root
RUN pip install -r requirements.txt
RUN chmod -R 777 /home/albireo


USER albireo
RUN echo "Setting up config file..."
RUN cp config/config-sample-vagrant.yml config/config.yml
RUN echo "Initialing database..."
USER root
RUN /etc/init.d/postgresql start && python tools.py --db-init && python tools.py --user-add admin 1234 && python tools.py --user-promote admin 3

EXPOSE 5000

# docker run --rm -it -v "`pwd`:/albireo" -p 127.0.0.1:5000:5000 albireo
