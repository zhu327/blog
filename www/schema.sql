-- mysql -u root -p < schema.sql

drop database if exists boz;

create database boz;

use boz;

grant select, insert, update, delete on boz.* to 'root'@'localhost' identified by '';

create table `users` (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `admin` bool  not null,
    `name` varchar(50) not null,
    `created` real not null,
    unique key `idx_email` (`email`),
    key `idx_created` (`created`),
    primary key(`id`)
) engine=innodb default charset=utf8;

create table `blogs` (
    `id` int(10) not null auto_increment,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `title` varchar(50) not null,
    `summary` mediumtext not null,
    `content` text not null,
    `tags` varchar(50),
    `created` real not null,
    `year` int(5) not null,
    key `idx_created` (`created`),
    primary key(`id`)
) engine=innodb default charset=utf8;

create table `tag` (
    `id` int(10) not null auto_increment,
    `name` varchar(50) not null,
    `blogid` int(10) not null,
    primary key(`id`)
) engine=innodb default charset=utf8;
