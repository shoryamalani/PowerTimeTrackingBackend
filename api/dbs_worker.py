from dbs_scripts import write_and_read_to_database,execute_db,create_database
import dotenv
import os
import json
import psycopg2
import datetime
import pypika
from pypika import functions,Query
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )
def set_up_connection():
    # Path to .env file
    if not is_docker():
        dotenv_path = os.path.join(os.path.dirname(__file__), '../postgres/.env')
        # Load file from the path
        dotenv.load_dotenv(dotenv_path)
        # set up connection to postgres
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST_DEV'),
            database=os.environ.get('POSTGRES_DB'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD')
        )
        return conn

    else:

        # dotenv_path = os.path.join(os.path.dirname(__file__), '/postgres/.env')
        # print(dotenv_path)
        print(os.listdir())
        # # Load file from the path
        # print(dotenv.load_dotenv(dotenv_path,verbose=True))
        # print(dotenv.dotenv_values(dotenv_path).items())
        dotenv.load_dotenv()

        # set up connection to postgres
        print(os.environ)
        print(os.environ.get('DB_HOST'))

        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('POSTGRES_DB'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD'),
            port=os.environ.get('DB_PORT')
        )
        return conn

def get_db_version(conn):
    sys = pypika.Table("sys")
    query = Query.from_(sys).select('*')
    try:
        data = execute_db.execute_database_command(conn,query.get_sql())[1]
        return data.fetchone()[1]
    except:
        return 0    

def set_up_db_version_1(conn):
    sys_table = create_database.create_table_command("sys",[['id','int'],['version','int']],'id')
    
    conn = execute_db.execute_database_command(set_up_connection(),sys_table)
    conn[0].commit()
    sys = pypika.Table('sys')
    set_up_version = sys.insert([0,1])
    users_table = create_database.create_table_command("users",[['UUID','UUID'],['name','text'],['email','text'],['date_created','timestamp'],['privacy_status','text'],['last_login','timestamp'],['data','json']],'UUID')
    execute_db.execute_database_command(set_up_connection(),users_table)[0].commit()
    # add admin role
    leaderboards_table = create_database.create_table_command("leaderboards",[['id','SERIAL'],['name','text'],['time_period','text'],['data','json']],'id')
    execute_db.execute_database_command(set_up_connection(),leaderboards_table)[0].commit()
    # groups
    groups_table = create_database.create_table_command("groups",[['id','SERIAL'],['status','text'],['name','text'],['data','json']],'id')
    execute_db.execute_database_command(set_up_connection(),groups_table)[0].commit()

    execute_db.execute_database_command(set_up_connection(),set_up_version.get_sql())[0].commit()


def set_db_version(version):
    conn = set_up_connection()
    sys = pypika.Table('sys')
    query = sys.update().set(sys.version,version)
    execute_db.execute_database_command(conn,query.get_sql())[0].commit()

def db_init():
    conn = set_up_connection()
    print(get_db_version(conn))
    if get_db_version(conn) < 1:
        set_up_db_version_1(conn)
def get_all_users():
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.from_(users).select('*')
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    return data.fetchall()

def get_all_events():
    conn = set_up_connection()
    events = pypika.Table('events')
    query = Query.from_(events).select('*')
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    return data.fetchall()

def get_all_due_dates():
    conn = set_up_connection()
    due_dates = pypika.Table('due_dates')
    query = Query.from_(due_dates).select('*')
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    return data.fetchall()

def get_all_roles():
    conn = set_up_connection()
    roles = pypika.Table('users_roles')
    query = Query.from_(roles).select('*')
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    return data.fetchall()

def get_user_by_id(user_id):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.from_(users).select('*').where(users.uuid == user_id)
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    user = data.fetchone()
    if user:
        return user
    else:
        return None

def create_user(name,privacy_status,data):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.into(users).columns('name','date_created','privacy_status','last_login','data').insert(name,functions.Now(),privacy_status,functions.Now(),json.dumps(data))
    print(query.get_sql()+" RETURNING UUID;")
    [conn,cur] = execute_db.execute_database_command(conn,query.get_sql()+" RETURNING uuid as id;")
    conn.commit()
    data = cur.fetchone()[0]
    print(data)
    return data
    return cur.fetchone()[0]
    return conn.cursor().lastrowid

def add_role_to_user(email,role_id):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.int(users).columns('role').set(role_id).where(users.email == email)


def get_user_by_email(email):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.from_(users).select('*').where(users.email == email)
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    user = data.fetchone()
    if user:
        return user
    else:
        return None

def get_user_count():
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.from_(users).select(functions.Count('*'))
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    return data.fetchone()[0]
    
def add_user(name,email,google_access_token,role,data):
    """add a user to the database

    Args:
        name (string): name
        email (string): email
        google_access_token (string): token
        role (uuid): uuid of role
        data (object): any data
    """
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.into(users).columns('name','email','google_access_token','role','data','date_created','last_login').insert(name,email,google_access_token,role,data,functions.Now(),functions.Now())
    execute_db.execute_database_command(conn,query.get_sql())[0].commit()


def set_user_display_name(user_id,display_name):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.update(users).set(users.name,display_name).where(users.uuid == user_id)
    execute_db.execute_database_command(conn,query.get_sql())[0].commit()

def get_users_by_name(name):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.from_(users).select('*').where(users.name == name)
    data = execute_db.execute_database_command(conn,query.get_sql())[1]
    users = data.fetchall()
    if users:
        return users
    else:
        return None
    
def set_user_privacy_status(user_id,privacy_status):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.update(users).set(users.privacy_status,privacy_status).where(users.uuid == user_id)
    execute_db.execute_database_command(conn,query.get_sql())[0].commit()

def set_user_data(user_id,data):
    conn = set_up_connection()
    users = pypika.Table('users')
    query = Query.update(users).set(users.data,json.dumps(data)).where(users.uuid == user_id)
    execute_db.execute_database_command(conn,query.get_sql())[0].commit()