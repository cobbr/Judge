#!/usr/bin/python

from __future__ import print_function
from ftplib import FTP
from StringIO import StringIO
import sqlite3, dns.resolver, requests
from dns.exception import DNSException
from threading import Thread
from time import sleep
from flask import Flask, render_template

app = Flask(__name__)

def database_create():
    """
    Create the backend ./data/debugger.db sqlite database
    """
    db = database_connect()
    with app.open_resource('./data/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def database_connect():
        """
        Connect with the backend ./debugger.db sqlite database and return the
        connection object.
        """
        try:
            # set the database connectiont to autocommit w/ isolation level
            conn = sqlite3.connect('./data/debugger.db')
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print("Error connecting to database. Must run 'flask setup' prior to running.",file=sys.stderr)
            sys.exit()

def execute_db_query(query, args=None):
    """
    Execute the supplied query on the provided db conn object
    with optional args for a paramaterized query.
    """
    conn = database_connect()
    cur = conn.cursor()
    if(args):
        cur.execute(query, args)
    else:
        cur.execute(query)
    conn.commit()
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


@app.context_processor
def utility_processor():    
    return dict(execute_db_query=execute_db_query)
        
@app.cli.command('setup')
def setup():
    print('Initializing database...')
    database_create()
    print('Done.')
    print('Setup complete.')
    
    
@app.route('/configure', methods=['GET'])
def configure():
    # get from db
    return render_template('configure.html')

@app.route('/teamadd', methods=['POST'])
def add_team():
    # add team
    return configure()

@app.route('/teamremove', methods=['POST'])
def remove_team():
    # del team
    return configure()

@app.route('/serviceadd', methods=['POST'])
def add_service():
    # add service
    return configure()

@app.route('/serviceremove', methods=['POST'])
def remove_service():
    # remove service
    return configure()

@app.route('/')
def scoreboard():
    # get from db
    return render_template('scoreboard.html')

def poll():
    while True:
        sleep(5)
        for service in execute_db_query('select * from service where service_active = 1'):
            row = execute_db_query('select * from service_type join service ON (service_type.service_type_id = service.service_type_id) where service.service_type_id = ?', [service['service_type_id']])[0]
            if row:
                id = row['service_id']
                type = row['service_type_name']
                server = row['service_connection']
                request = row['service_request']
                eresult = row['service_expected_result']
                result = ''
                if type == 'dns':
                    try:
                        resolv = dns.resolver.Resolver()
                        resolv.nameservers = [server]
                        resolv.timeout = 5
                        resolv.lifetime = 5
                        answers = resolv.query(request, 'A')
                        for rdata in answers:
                            result = rdata.to_text()
                    except DNSException:
                        print('Failed - DNS Request: ' + request + ' Server: ' + server)
                elif type == 'http':
                    result = requests.get('http://' + server + request)
                elif type == 'https':
                    result = requests.get('https://' + server + request)
                elif type == 'ftp':
                    ftp = FTP(server)
                    ftp.login()
                    resultStringIO = StringIO()
                    ftp.retrbinary('RETR ' + request, resultStringIO.write)
                    result = resultStringIO.getvalue()
                elif type == 'mysql':
                    print('mysql')
                if eresult == result:
                    execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [id])
                else:
                    execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [id])
                    print('result: ' + result + ' did not match expected: ' + eresult)


if __name__ == "__main__":
    thread = Thread(target=poll)
    thread.setDaemon(True)
    thread.start()
    app.run(host='0.0.0.0')

