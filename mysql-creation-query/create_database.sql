-- create a druid database, make sure to use utf8mb4 as encoding
CREATE DATABASE IF NOT EXISTS druid DEFAULT CHARACTER SET utf8mb4;

-- create a druid user
CREATE USER IF NOT EXISTS 'druid'@'localhost' IDENTIFIED BY '*****************';

-- grant the user all the permissions on the database we just created
GRANT ALL PRIVILEGES ON druid.* TO 'druid'@'localhost';
