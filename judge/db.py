import sqlite3, yaml

# Database functions
def database_create():
    """
    Create the backend ./data/debugger.db sqlite database
    """
    db = database_connect()
    with open('./data/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def database_populate():
    """
    Populate the database with default data.
    """
    db = database_connect()
    with open('services.yaml', mode='r') as yaml_config:
        cfg = yaml.load(yaml_config)
    for team in cfg['teams']:
        execute_db_query('insert into team(team_name) VALUES(?)', [team['team_name']])
    for service in cfg['services']:

        execute_db_query('insert into service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) '
        +'VALUES((select service_type_id from service_type where service_type_name = ?), (select team_id from team where team_name = ?),?,?,?,?)'
        , [service['service_type_name'], service['team_name'], service['service_name'], service['service_connection'], service['service_request'], service['service_expected_result']])

def database_connect():
    """
    Connect with the backend ./debugger.db sqlite database and return the
    connection object.
    """
    try:
        conn = sqlite3.connect('./data/debugger.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print "Error connecting to database. Must run 'flask setup' prior to running. Error message: " + repr(e)
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
