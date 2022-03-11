DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `room`;
DROP TABLE IF EXISTS `room_user`;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `token` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`)
);

CREATE TABLE `room` (
  `room_id` bigint NOT NULL AUTO_INCREMENT,
  `live_id` int DEFAULT NULL,
  `joined_user_count` int DEFAULT NULL,
  `max_user_count` int DEFAULT 4,
  `token` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `token` (`token`)
);

CREATE TABLE `room_user`(
  `room_id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  `select_difficulty` int DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `user_id` (`user_id`)
);

INSERT INTO `user` (`name`,`token`,`leader_card_id`) values ("しずる", "76f52c6b-a8f9-4c5f-8ecf-48ac055bb34e", "0");
INSERT INTO `user` (`name`,`token`,`leader_card_id`) values ("れの", "02ed6fc8-9fff-4032-a06d-0263842ebced", "1");
