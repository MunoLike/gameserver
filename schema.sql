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
  `host_id` bigint DEFAULT NULL ,
  `joined_user_count` int DEFAULT NULL,
  `max_user_count` int DEFAULT 4,
  `wait_status` int DEFAULT 1,
  `token` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `token` (`token`)
);

CREATE TABLE `room_user`(
  `room_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  `select_difficulty` int DEFAULT NULL,
  `judge_count_list` json DEFAULT NULL,
  `score` int DEFAULT -1,
  PRIMARY KEY (`room_id`, `user_id`)
);

-- INSERT INTO `user` (`name`,`token`,`leader_card_id`) values ("むの", "c687c27b-cbb2-4307-b07e-38f4d8fc0a2c", 1000);
-- INSERT INTO `user` (`name`,`token`,`leader_card_id`) values ("muno", "315f6417-7f8c-4d34-b7af-5b82485af12a", 1000);

-- INSERT INTO `room` (`live_id`, `host_id`,`joined_user_count`, `max_user_count`, `wait_status`, `token`) values (3, 1, 1, 4, 1, "4330eb55-52e6-48e6-b150-597cd1fec08f");
-- INSERT INTO `room_user` SET `room_id` = 1, `user_id` = 1, `name` = "MunoLike", `leader_card_id` = 0, `select_difficulty` = 1;
