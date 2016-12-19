CREATE TABLE team (
    team_id INTEGER PRIMARY KEY ASC,
    team_name varchar(255) NOT NULL
);

CREATE TABLE service_type (
    service_type_id INTEGER PRIMARY KEY ASC,
    service_type_name varchar(255) NOT NULL
);

CREATE TABLE service (
    service_id INTEGER PRIMARY KEY ASC,
    service_type_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    service_name varchar(255) NOT NULL,
    service_connection varchar(255) NOT NULL,
    service_request varchar(255) NOT NULL,
    service_expected_result varchar(255) NOT NULL,
    service_active INTEGER NOT NULL,
    FOREIGN KEY (service_type_id) REFERENCES service_type(service_type_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);

CREATE TABLE poll (
    poll_id INTEGER PRIMARY KEY ASC,
    poll_score INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    FOREIGN KEY (service_id) REFERENCES service(service_id)
);

INSERT INTO service_type(service_type_name) VALUES('dns');
INSERT INTO service_type(service_type_name) VALUES('http');
INSERT INTO service_type(service_type_name) VALUES('https');
INSERT INTO service_type(service_type_name) VALUES('ftp');
INSERT INTO service_type(service_type_name) VALUES('mysql');
INSERT INTO service_type(service_type_name) VALUES('ssh');

INSERT INTO team(team_name) VALUES('team');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result, service_active) VALUES(1,1,'internal dns','172.25.21.27','addns.ccdc.cobbr.io', '172.25.21.27',1);
