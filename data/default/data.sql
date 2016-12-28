INSERT INTO team(team_name) VALUES('Baylor');

INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'internal dns - addns.ccdc.cobbr.io','172.25.21.27','addns.ccdc.cobbr.io','172.25.21.27');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'internal dns - mail.ccdc.cobbr.io','172.25.21.27','mail.ccdc.cobbr.io', '172.25.21.39');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'internal dns - web.ccdc.cobbr.io','172.25.21.27','web.ccdc.cobbr.io', '172.25.21.3');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'internal dns - ftp.ccdc.cobbr.io','172.25.21.27','ftp.ccdc.cobbr.io', '172.25.21.9');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'dmz dns - www.ecomm.cobbr.io','172.25.21.23','www.ecomm.cobbr.io', '172.25.21.11');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'dmz dns - dns.ecomm.cobbr.io','172.25.21.23','dns.ecomm.cobbr.io', '172.25.21.23');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'internal dns - ccdc.cobbr.io','172.25.21.27','ccdc.cobbr.io', '172.25.21.100');
INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'dns'),1,'dmz dns - ecomm.cobbr.io','172.25.21.23','ecomm.cobbr.io', '172.25.21.100');


INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'http'),1,'dmz http - www.ecomm.cobbr.io','172.25.21.11','/', 'data/uploads/default/www_ecomm_cobbr_io');


INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'ftp'),1,'internal ftp - ftp.ccdc.cobbr.io','172.25.21.9','/helloworld.txt', 'data/uploads/default/helloworld.txt');

INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES((SELECT service_type_id from service_type where service_type_name = 'mail'),1,'internal mail - mail.ccdc.cobbr.io','172.25.21.39','ccdc@ccdc.cobbr.io:ccdc@ccdc.cobbr.io:message', 'message');
