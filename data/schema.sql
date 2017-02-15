-- Judge v0.1 - schema.sql
-- Author: Ryan Cobb (@cobbr_io)
-- Project Home: https://github.com/cobbr/Judge
-- License: GNU GPLv3

CREATE TABLE team (
    team_id INTEGER PRIMARY KEY ASC,
    team_name TEXT NOT NULL
);

CREATE TABLE service_type (
    service_type_id INTEGER PRIMARY KEY ASC,
    service_type_name TEXT NOT NULL
);

CREATE TABLE service (
    service_id INTEGER PRIMARY KEY ASC,
    service_type_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    service_connection TEXT NOT NULL,
    service_request TEXT NOT NULL,
    service_expected_result TEXT NOT NULL,
    service_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (service_type_id) REFERENCES service_type(service_type_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);

CREATE TABLE poll (
    poll_id INTEGER PRIMARY KEY ASC,
    poll_score INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    poll_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES service(service_id)
);

CREATE TABLE error (
    error_id INTEGER PRIMARY KEY ASC,
    service_id INTEGER NOT NULL,
    error_message TEXT NOT NULL,
    error_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES service(service_id)
);

INSERT INTO service_type(service_type_name) VALUES('dns');
INSERT INTO service_type(service_type_name) VALUES('http');
INSERT INTO service_type(service_type_name) VALUES('https');
INSERT INTO service_type(service_type_name) VALUES('ftp');
INSERT INTO service_type(service_type_name) VALUES('mail');
