"""
Read the set of email addresses in addresses.csv.
Create an empty database to be filled with Google results.

Populate the database with populate_database.

Google results are further refined in parse.py.

# 
Data format:
- a database is a Dict with email as the key, list of GoogleResult as value.
- addresses.csv:
Country;CompanyName;FirstName;LastName;Title;EmailAddress
Germany;Company1;first_name_1;last_name_1;Dr.;foo1@bar.com
Italy;Company1;first_name_2;last_name_2;Dr.;foo2@bar.com
Switzerland;Company2;first_name_3;last_name_3;Mr.;foo3@bar.com
France;Company2;first_name_4;last_name_4;Dr.;foo4@bar.com
"""

import pandas as pd
import pickle
import sys
import subprocess

from google_query import *
import urllib
import urllib.error


def read_addresses(addresses_path='addresses.csv'):
    """Read personal data from addresses.csv"""
    df = pd.read_csv(addresses_path, sep=';', na_filter=False)
    return df


def refresh_VPN():
    """Disconnect and reconnect the VPN"""
    print('Refreshing VPN!')
    path = r"C:\Program Files\CyberGhost 6\CyberGhost.exe"

    print('Disconnecting...')
    subprocess.run([path, "/disconnect"], check=False)

    # print('Reconnecting...')
    # res = subprocess.run([path, "/connect"], check=False)
    # print('done.')


def write_database(db, db_path='database.pickle'):
    """Write the Google result database to disk"""
    with open(db_path, 'wb') as f:
        pickle.dump(db, f)
    print("Wrote to disk.")


def make_new_database(addresses_path='addresses.csv'):
    """Make empty database from emails in .csv form

    A database is a dictionary with email as the key, list of GoogleResult as value
    """

    df = read_addresses(addresses_path)
    db = dict.fromkeys(df['EmailAddress'].values)

    print("Made new database.")
    return db


def load_database(db_path='database.pickle'):
    """Load the saved database of queried results"""
    with open(db_path, 'rb') as f:
        db = pickle.load(f)
    print("Loaded database: {0} entries".format(len(db)))
    return db


def get_name(email, single_string=False, df=None):
    """Get dictionary of personal details from e-mail"""
    if (df is None):
        df = read_addresses()

    row = df[df['EmailAddress'].values == email]

    def sanitize_string(s):
        """Return the string, or a blank if invalid"""
        try:
            return s + ''
        except TypeError:
            return ''

    first = sanitize_string(row['FirstName'].values[0])
    last = sanitize_string(row['LastName'].values[0])
    company = sanitize_string(row['CompanyName'].values[0])
    country = sanitize_string(row['Country'].values[0])

    if single_string:
        return first + ' ' + last
    else:
        return {
            'first': first,
            'last': last,
            'country': country,
            'company': company
        }


def populate_database(db, query='email', write=True, db_path='database.pickle'):
    """Fill the database with Google queries"""
    emails = list(db.keys())
    df = read_addresses()

    print('Populating database: {0} records.'.format(len(db)))

    for i, email in enumerate(emails):
        print('Record {0} of {1}.'.format(i, len(emails)))
        details = get_name(email, df=df)

        # Skip invalid fields
        if not isinstance(email, str):
            continue

        # Skip already filled results
        if db[email] is not None:
            # print('Email {0} already known.'.format(email))
            continue

        try:
            # Create the Google query
            dict_query = {
                'email': email,
                'name+surname+email': '{0} {1} "{2}"'.format(details['first'], details['last'], email)
            }
            try:
                query_string = dict_query[query]
            except KeyError as e:
                print('query must be in {0}', list(dict_query.keys()))

            print('Querying email {0} ({1}/{2}): query \'{3}\''.format(email, i, len(emails), query_string))
            result = do_google_query(query_string)

            # result is a list of GoogleResult objects

            print("Got {0} results.".format(len(result)))
            db[email] = result

            # Update after each query
            if write:
                write_database(db, db_path=db_path)

        except urllib.error.HTTPError as e:
            print('Caught HTTP error: {0}'.format(e))

            if e.code == 503:
                # Too many requests: must change IP
                # TODO: do it automatically
                refresh_VPN()
                sys.exit(-1)

    print('Finished populating database.')


def database_stats(db):
    """Compute basic stats on the database"""
    emails = list(db.keys())

    non_null = 0
    for i, email in enumerate(emails):
        if db[email] is not None:
            non_null += 1

    print("Total entries: {0}".format(len(db)))
    print("Non-null entries: {0}".format(non_null))


if __name__ == '__main__':

    # Read emails from .csv, create empty database and store to disk
    db = make_new_database()
    write_database(db)

    # Testing: try first 10 emails and overwrite the database
    # db = {e: db[e] for e in list(db.keys())[1:10]}
    # write_database(db)

    # Load the database from disk
    db = load_database()
    database_stats(db)

    # emails = list(db.keys())

    # Start Google queries on emails in database

    # populate_database(db, query='email', write=True)
    populate_database(db, query='name+surname+email', write=True)

    print('Script finished. Now you can start parsing Google results.')
