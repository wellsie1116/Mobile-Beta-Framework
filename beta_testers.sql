-- phpMyAdmin SQL Dump
-- version 3.3.7deb5build0.10.10.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Sep 05, 2011 at 08:49 AM
-- Server version: 5.1.49
-- PHP Version: 5.3.3-1ubuntu9.5

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `beta_testers`
--

-- --------------------------------------------------------

--
-- Stand-in structure for view `android_devices`
--
CREATE TABLE IF NOT EXISTS `android_devices` (
`User's Name` varchar(100)
,`User's Email` varchar(100)
,`User Verified` tinyint(1)
,`Device Verified` tinyint(1)
,`OS Info` varchar(10000)
,`Model` varchar(10000)
,`Carrier` varchar(100)
,`Build Number` int(11)
);
-- --------------------------------------------------------

--
-- Table structure for table `builds`
--

CREATE TABLE IF NOT EXISTS `builds` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `platform` int(11) NOT NULL,
  `build_number` int(11) NOT NULL,
  `published` datetime NOT NULL,
  `official` tinyint(1) NOT NULL,
  `view_url` varchar(10000) DEFAULT NULL,
  `download_url` varchar(10000) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_platform` (`platform`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=13 ;

-- --------------------------------------------------------

--
-- Table structure for table `carriers`
--

CREATE TABLE IF NOT EXISTS `carriers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `identifier` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identifier_UNIQUE` (`identifier`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=14 ;

-- --------------------------------------------------------

--
-- Table structure for table `devices`
--

CREATE TABLE IF NOT EXISTS `devices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(100) NOT NULL,
  `os_info` varchar(10000) DEFAULT NULL,
  `model` varchar(10000) DEFAULT NULL,
  `verified` tinyint(1) NOT NULL,
  `verification_code` varchar(100) NOT NULL,
  `auth_token` varchar(100) NOT NULL,
  `user` int(11) NOT NULL,
  `carrier` int(11) DEFAULT NULL,
  `build` int(11) NOT NULL,
  `platform` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identifier_UNIQUE` (`identifier`),
  UNIQUE KEY `verification_code_UNIQUE` (`verification_code`),
  UNIQUE KEY `auth_token_UNIQUE` (`auth_token`),
  KEY `FK_device_user` (`user`),
  KEY `FK_device_carrier` (`carrier`),
  KEY `FK_device_build` (`build`),
  KEY `FK_device_platform` (`platform`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=35 ;

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE IF NOT EXISTS `feedback` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device` int(11) NOT NULL,
  `build` int(11) NOT NULL,
  `time` datetime NOT NULL,
  `content` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_build` (`build`),
  KEY `FK_device` (`device`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `ios_devices`
--
CREATE TABLE IF NOT EXISTS `ios_devices` (
`User's Name` varchar(100)
,`User's Email` varchar(100)
,`User Verified` tinyint(1)
,`Device Verified` tinyint(1)
,`OS Info` varchar(10000)
,`Model` varchar(10000)
,`Carrier` varchar(100)
,`Build Number` int(11)
);
-- --------------------------------------------------------

--
-- Table structure for table `platforms`
--

CREATE TABLE IF NOT EXISTS `platforms` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `identifier` varchar(100) NOT NULL,
  `owner_email` varchar(100) NOT NULL,
  `publish_key` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identifier_UNIQUE` (`identifier`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=6 ;

-- --------------------------------------------------------

--
-- Table structure for table `test_results`
--

CREATE TABLE IF NOT EXISTS `test_results` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device` int(11) NOT NULL,
  `build` int(11) NOT NULL,
  `time` datetime NOT NULL,
  `content` longtext,
  `pass` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_test_results_build` (`build`),
  KEY `FK_test_results_device` (`device`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7 ;

-- --------------------------------------------------------

--
-- Table structure for table `updates`
--

CREATE TABLE IF NOT EXISTS `updates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device` int(11) NOT NULL,
  `from_build` int(11) NOT NULL,
  `to_build` int(11) NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_updates_device` (`device`),
  KEY `FK_updates_from_build` (`from_build`),
  KEY `FK_updates_to_build` (`to_build`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `created` datetime NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `verification_code` varchar(100) NOT NULL,
  `name_change_code` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_UNIQUE` (`email`),
  UNIQUE KEY `verification_code_UNIQUE` (`verification_code`),
  UNIQUE KEY `name_change_code_UNIQUE` (`name_change_code`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=43 ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `wp7_devices`
--
CREATE TABLE IF NOT EXISTS `wp7_devices` (
`User's Name` varchar(100)
,`User's Email` varchar(100)
,`User Verified` tinyint(1)
,`Device Verified` tinyint(1)
,`OS Info` varchar(10000)
,`Model` varchar(10000)
,`Carrier` varchar(100)
,`Build Number` int(11)
);
-- --------------------------------------------------------

--
-- Structure for view `android_devices`
--
DROP TABLE IF EXISTS `android_devices`;

CREATE ALGORITHM=UNDEFINED DEFINER=`jimmy`@`174.61.156.116` SQL SECURITY DEFINER VIEW `android_devices` AS select `u`.`name` AS `User's Name`,`u`.`email` AS `User's Email`,`u`.`verified` AS `User Verified`,`d`.`verified` AS `Device Verified`,`d`.`os_info` AS `OS Info`,`d`.`model` AS `Model`,`c`.`name` AS `Carrier`,`b`.`build_number` AS `Build Number` from ((((`devices` `d` join `users` `u` on((`d`.`user` = `u`.`id`))) join `carriers` `c` on((`d`.`carrier` = `c`.`id`))) join `builds` `b` on(((`d`.`build` = `b`.`id`) and (`d`.`platform` = `b`.`platform`)))) join `platforms` `p` on((`d`.`platform` = `p`.`id`))) where (`p`.`identifier` = 'android');

-- --------------------------------------------------------

--
-- Structure for view `ios_devices`
--
DROP TABLE IF EXISTS `ios_devices`;

CREATE ALGORITHM=UNDEFINED DEFINER=`jimmy`@`174.61.156.116` SQL SECURITY DEFINER VIEW `ios_devices` AS select `u`.`name` AS `User's Name`,`u`.`email` AS `User's Email`,`u`.`verified` AS `User Verified`,`d`.`verified` AS `Device Verified`,`d`.`os_info` AS `OS Info`,`d`.`model` AS `Model`,`c`.`name` AS `Carrier`,`b`.`build_number` AS `Build Number` from ((((`devices` `d` join `users` `u` on((`d`.`user` = `u`.`id`))) join `carriers` `c` on((`d`.`carrier` = `c`.`id`))) join `builds` `b` on(((`d`.`build` = `b`.`id`) and (`d`.`platform` = `b`.`platform`)))) join `platforms` `p` on((`d`.`platform` = `p`.`id`))) where (`p`.`identifier` = 'ios');

-- --------------------------------------------------------

--
-- Structure for view `wp7_devices`
--
DROP TABLE IF EXISTS `wp7_devices`;

CREATE ALGORITHM=UNDEFINED DEFINER=`jimmy`@`174.61.156.116` SQL SECURITY DEFINER VIEW `wp7_devices` AS select `u`.`name` AS `User's Name`,`u`.`email` AS `User's Email`,`u`.`verified` AS `User Verified`,`d`.`verified` AS `Device Verified`,`d`.`os_info` AS `OS Info`,`d`.`model` AS `Model`,`c`.`name` AS `Carrier`,`b`.`build_number` AS `Build Number` from ((((`devices` `d` join `users` `u` on((`d`.`user` = `u`.`id`))) join `carriers` `c` on((`d`.`carrier` = `c`.`id`))) join `builds` `b` on(((`d`.`build` = `b`.`id`) and (`d`.`platform` = `b`.`platform`)))) join `platforms` `p` on((`d`.`platform` = `p`.`id`))) where (`p`.`identifier` = 'wp7');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `builds`
--
ALTER TABLE `builds`
  ADD CONSTRAINT `FK_build_platform` FOREIGN KEY (`platform`) REFERENCES `platforms` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Constraints for table `devices`
--
ALTER TABLE `devices`
  ADD CONSTRAINT `FK_device_build` FOREIGN KEY (`build`) REFERENCES `builds` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_device_platform` FOREIGN KEY (`platform`) REFERENCES `platforms` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_device_user` FOREIGN KEY (`user`) REFERENCES `users` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_device_carrier` FOREIGN KEY (`carrier`) REFERENCES `carriers` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `FK_feedback_device` FOREIGN KEY (`device`) REFERENCES `devices` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_feedback_build` FOREIGN KEY (`build`) REFERENCES `builds` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Constraints for table `test_results`
--
ALTER TABLE `test_results`
  ADD CONSTRAINT `FK_test_results_device` FOREIGN KEY (`device`) REFERENCES `devices` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_test_results_build` FOREIGN KEY (`build`) REFERENCES `builds` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Constraints for table `updates`
--
ALTER TABLE `updates`
  ADD CONSTRAINT `FK_updates_from_build` FOREIGN KEY (`from_build`) REFERENCES `builds` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_updates_device` FOREIGN KEY (`device`) REFERENCES `devices` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  ADD CONSTRAINT `FK_updates_to_build` FOREIGN KEY (`to_build`) REFERENCES `builds` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
