-- mysql -u root -p < schema.sql

create table `user` (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `name` varchar(50) not null,
    primary key(`id`)
) engine=MyISAM default charset=utf8;

create table `blogs` (
    `id` int(10) not null auto_increment,
    `title` varchar(50) not null,
    `summary` mediumtext not null,
    `content` text not null,
    `tags` varchar(50),
    `created` datetime DEFAULT NULL,
    primary key(`id`)
) engine=MyISAM default charset=utf8;

create table `tags` (
    `id` int(10) not null auto_increment,
    `tag` varchar(50) not null,
    `blog` int(10) not null,
    primary key(`id`)
) engine=MyISAM default charset=utf8;

INSERT INTO `user` (`id`, `email`, `password`, `name`)
VALUES
	('20140911', 'admin@example.com', 'e10adc3949ba59abbe56e057f20f883e', 'admin');
