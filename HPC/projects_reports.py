#!/usr/bin/python

import MySQLdb
import os
import ConfigParser
import optparse
from collections import defaultdict
import csv

# Set up a parser for our configuration file.
parse = ConfigParser.SafeConfigParser()

# Parse the configuration file.
parse.read('/etc/myami/sinedon.cfg')

parser = optparse.OptionParser()
parser.add_option("--scope", dest="scope", help="Path scope to restrict reports to.")

options, args = parser.parse_args()

def retrieve_all_projects():
    """
    Return all the projects in the database.The returned object is a dictionary of tuples, 
    where the key is the project_id and the value is a tuple containing the name, 
    short_description, and long_description.
    """

    # Open database connection
    db = MySQLdb.connect(host=parse.get('global', 'host'), user=parse.get('global', 'user'), 
                         passwd=parse.get('global', 'passwd'), db=parse.get('projectdata', 'db'))
    # Prepare a cursor object using the cursor() method
    cursor = db.cursor()
    """
    Temporary defaultdict with lists as values, which will be converted to tuples. 
    This way you are appending to lists and not recreating tuples.
    """
    
    d1 = defaultdict(list)
    try:
        # Execute the SQL command to get all projects
        cursor.execute("SELECT DEF_id, name, short_description, long_description FROM projects")
        # Fetch all the rows in a tuple of tuples.
        results = cursor.fetchall()
        for row in results:
            d1[row[0]].append(row[1])
            d1[row[0]].append(row[2])
            d1[row[0]].append(row[3])
    except:
        raise Exception('Unable to fetch data from the projects table.')
    finally:
        # Disconnect from database
        db.close()
    
    # Convert the temporary defaultdict that contains lists as values to tuples.
    projects = dict((k, tuple(v)) for k, v in d1.iteritems())
    cursor.close()
    # projects is a dictionary of tuples.
    # projects = {project_id: (name, short_description, long_description), }
    return projects


def retrieve_all_projectowners():
    """
    Return all the projects and their owners. The returned object is a dictionary of tuples, 
    where the key is the project_id and the value is a tuple containing the user_id of those 
    users that own the project.
    """

    # Open database connection
    db = MySQLdb.connect(host=parse.get('global', 'host'), user=parse.get('global', 'user'), 
                         passwd=parse.get('global', 'passwd'), db=parse.get('projectdata', 'db'))
    # Prepare a cursor object using the cursor() method
    cursor = db.cursor()
    """
    Temporary defaultdict with lists as values, which will be converted to tuples. 
    This way you are appending to lists and not recreating tuples.
    """

    d1 = defaultdict(list)
    try:
        # Execute the SQL command to get all projects
        cursor.execute("SELECT `REF|projects|project`, `REF|leginondata|UserData|user` 
                       FROM projectowners")
        # Fetch all the rows in a tuple of tuples.
        results = cursor.fetchall()
        for row in results:
            d1[row[0]].append(row[1])
    except:
        raise Exception('Unable to fetch data from the projectowners table.')
    finally:
        # Disconnect from database
        db.close()

    # Convert the temporary defaultdict that contains lists as values to tuples.
    project_owners = dict((k, tuple(v)) for k, v in d1.iteritems())
    cursor.close()
    # project_owners is a dictionary of tuples.
    # project_owners = {project_id: (user_id,),}
    return project_owners

def retrieve_all_projectexperiments():
    """
    Get the project DEF_id and session DEF_id for all projectexperiment entries.
    The returned object is a dictionary of tuples, where the key is the project_id 
    and the value is a tuple containing the session_id of the sessions associated 
    with the project.
    """

    # Open database connection
    db = MySQLdb.connect(host=parse.get('global', 'host'), user=parse.get('global', 'user'), 
                         passwd=parse.get('global', 'passwd'), db=parse.get('projectdata', 'db'))
    # Prepare a cursor object using the cursor() method
    cursor = db.cursor()
    """
    Temporary defaultdict with lists as values, which will be converted to tuples. 
    This way you are appending to lists and not recreating tuples.
    """

    d1 = defaultdict(list)
    try:
        # Execute the SQL command
        cursor.execute("SELECT `REF|projects|project`, `REF|leginondata|SessionData|session` 
                       FROM projectexperiments")
        # Fetch all the rows in a tuple of tuples.
        results = cursor.fetchall()
        cursor.close()
        for row in results:
            d1[row[0]].append(row[1])
    except:
        raise Exception('Unable to fetch data from the projectexperiments table.')
    finally:
        # Disconnect from database
        db.close()
    # Convert the temporary defaultdict that contains lists as values to tuples.
    project_experiments = dict((k, tuple(v)) for k, v in d1.iteritems())
    # project_experiments = {project_id: (session_id,),}
    return project_experiments

def retrieve_all_users():
    """
    Get all the users from the database. The returned object is a dictionary of tuples, 
    where the key is the user_id and the value is a tuple containing the username, 
    firstname, and lastname of the user.
    :return:
    """

    # Open database connection
    db = MySQLdb.connect(host=parse.get('global', 'host'), user=parse.get('global', 'user'), 
                         passwd=parse.get('global', 'passwd'), db=parse.get('leginondata', 'db'))
    # Prepare a cursor object using the cursor() method
    cursor = db.cursor()
    """
    Temporary defaultdict with lists as values, which will be converted to tuples. 
    This way you are appending to lists and not recreating tuples.
    """

    d1 = defaultdict(list)
    try:
        # Execute the SQL command
        cursor.execute("SELECT DEF_id, username, firstname, lastname FROM UserData")
        # Fetch all the rows in a tuple of tuples.
        results = cursor.fetchall()
        for row in results:
            d1[row[0]].append(row[1])
            d1[row[0]].append(row[2])
            d1[row[0]].append(row[3])
    except:
        raise Exception('Unable to fetch data from the UserData table.')
    finally:
        # Disconnect from database
        db.close()
    # Convert the temporary defaultdict that contains lists as values to tuples.
    users = dict((k, tuple(v)) for k, v in d1.iteritems())
    # users = {user_id: (username, firstname, lastname),}
    return users

def retrieve_all_sessions():
    """
    For all SessionData entries get the session DEF_id, session name, UserData DEF_id, 
    session image path, and session frame path. The returned object is a dictionary of 
    tuples, where the key is the session_id and the value is a tuple containing the name, 
    user_id, image path, and frame path for the session.

    :rtype: dict
    :return:
    """

    # Open database connection
    db = MySQLdb.connect(host=parse.get('global', 'host'), user=parse.get('global', 'user'), 
                         passwd=parse.get('global', 'passwd'), db=parse.get('leginondata', 'db'))
    # Prepare a cursor object using the cursor() method
    cursor = db.cursor()
    """
    Temporary defaultdict with lists as values, which will be converted to tuples. 
    This way you are appending to lists and not recreating tuples.
    """

    d1 = defaultdict(list)
    try:
        # Execute the SQL command
        cursor.execute("SELECT DEF_id, name, `REF|UserData|user`, `image path`, `frame path` 
                       FROM SessionData")
        # Fetch all the rows in a tuple of tuples.
        results = cursor.fetchall()
        for row in results:
            d1[row[0]].append(row[1])
            d1[row[0]].append(row[2])
            d1[row[0]].append(row[3])
            d1[row[0]].append(row[4])
    except:
        raise Exception('Unable to fetch data from the SessionData table.')
    finally:
        # Disconnect from database
        db.close()
    # Convert the temporary defaultdict that contains lists as values to tuples.
    sessions = dict((k, tuple(v)) for k, v in d1.iteritems())
    # sessions = {session_id: (name, user_id, image path, frame path),}
    return sessions


def get_size(start_path='.'):
    """
    Return the size of the directory start_path in bytes.  This includes the subdirectories.

    :param start_path:
    :return:
    """

    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                pass
    return total_size


def main():
    # {project_id: (name, short_description, long_description),}
    projects = retrieve_all_projects()
    project_owners = retrieve_all_projectowners()
    project_experiments = retrieve_all_projectexperiments()
    users = retrieve_all_users()
    sessions = retrieve_all_sessions()

    for k, v in projects.iteritems():
        print "\nProject Name: {}".format(v[0])
        print "    Project Owned by: "
        # If the project has any owners associated with it.
        if k in project_owners:
            for x in project_owners[k]:
                try:
                    print "        {}".format(users[x][0])
                except KeyError:
                    pass
        else:
            print "        None"
        print "    Project Sessions:"
        # If the project has any sessions associated with it.
        if k in project_experiments:
            for x in project_experiments[k]:
                if options.scope and options.scope in sessions[x][2]:
                    try:
                        print "        {}".format(sessions[x][0])
                        print "        {}".format(users[sessions[x][1]][0])
                        if os.path.exists(os.path.dirname(sessions[x][2])):
                            print "        {} - {} bytes".format(os.path.dirname(sessions[x][2]), get_size(os.path.dirname(sessions[x][2])))
                        else:
                            print "        {} - Does Not Exist".format(os.path.dirname(sessions[x][2]))
                        if os.path.exists(os.path.dirname(sessions[x][3])):
                            print "        {} - {} bytes\n".format(os.path.dirname(sessions[x][3]), get_size(os.path.dirname(sessions[x][3])))
                        else:
                            print "        {} - Does Not Exist\n".format(os.path.dirname(sessions[x][3]))
                    except KeyError:
                        pass
                else:
                    try:
                        print "        {}".format(sessions[x][0])
                        print "        {}".format(users[sessions[x][1]][0])
                        if os.path.exists(os.path.dirname(sessions[x][2])):
                            print "        {} - {} bytes".format(os.path.dirname(sessions[x][2]), get_size(os.path.dirname(sessions[x][2])))
                        else:
                            print "        {} - Does Not Exist".format(os.path.dirname(sessions[x][2]))
                        if os.path.exists(os.path.dirname(sessions[x][3])):
                            print "        {} - {} bytes\n".format(os.path.dirname(sessions[x][3]), get_size(os.path.dirname(sessions[x][3])))
                        else:
                            print "        {} - Does Not Exist\n".format(os.path.dirname(sessions[x][3]))
                    except KeyError:
                        pass
        else:
            print "        None"


if __name__ == '__main__':
    main()
