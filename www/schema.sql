-- mysql -u root -p < schema.sql

drop database if exists boz;

create database boz;

use boz;

grant select, insert, update, delete on boz.* to 'root'@'localhost' identified by '';

create table `users` (
    `uid` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `admin` bool  not null,
    `name` varchar(50) not null,
    `created` real not null,
    unique key `idx_email` (`email`),
    key `idx_created` (`created`),
    primary key(`uid`)
) engine=innodb default charset=utf8;

create table `blogs` (
    `bid` int(10) not null auto_increment,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `title` varchar(50) not null,
    `content` text not null,
    `tags` varchar(50),
    `created` real not null,
    key `idx_created` (`created`),
    primary key(`bid`)
) engine=innodb default charset=utf8;

create table `tag` (
    `tid` int(10) not null auto_increment,
    `name` varchar(50) not null,
    unique key `idx_name` (`name`),
    primary key(`tid`)
) engine=innodb default charset=utf8;

create table `tagmap` (
    `id` int(10) not null auto_increment,
    `tid` int(10) not null,
    `bid` int(10) not null,
    primary key(`id`)
) engine=innodb default charset=utf8;
