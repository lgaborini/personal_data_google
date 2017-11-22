"""
Read the set of email addresses in addresses.csv.
Create an empty database to be filled with Google results.

Populate the database with populate_database(...).

Data format:
- a database is a Dict with email as the key, list of GoogleResult as value.

"""

import pandas as pd
import pickle
import sys
import subprocess

from google_query import *
import urllib
import urllib.error


def read_addresses():
    """Read personal data from addresses.csv"""
    df = pd.read_csv('addresses.csv', sep=';', na_filter=False)
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


def write_database(db):
    """Write the Google result database to disk"""
    with open('database.pickle', 'wb') as f:
        pickle.dump(db, f)
    print("Wrote to disk.")


def make_new_database():
    """Make empty database from emails in .csv form"""

    # A database is a dictionary with email as the key, list of GoogleResult as value
    df = read_addresses()
    db = dict.fromkeys(df['EmailAddress'].values)
    print("Made new database.")
    return db


def load_database(path='database.pickle'):
    """Load the saved database of queried results"""
    with open(path, 'rb') as f:
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


def populate_database(db, query='email', write=True):
    """Fill the database with Google queries"""
    emails = list(db.keys())
    df = read_addresses()

    for i, email in enumerate(emails):

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
            if query is 'email':
                query_string = email
            if query is 'name+surname+email':
                query_string = '{0} {1} "{2}"'.format(details.first, details.last, email)

            print('Querying email {0} ({1}/{2}): query"{3}"'.format(email, i, len(emails), query_string))
            result = do_google_query(query_string)

            # result is a list of GoogleResult objects

            print("Got {0} results.".format(len(result)))
            db[email] = result

            # Update after each query
            if write:
                write_database(db)

        except urllib.error.HTTPError as e:
            print('Caught HTTP error: {0}'.format(e))

            if e.code == 503:
                # Too many requests: must change IP
                # TODO: do it automatically
                refresh_VPN()
                sys.exit(-1)


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
    # db = make_new_database()
    # write_database(db)

    # Load the database from disk
    db = load_database()
    database_stats(db)

    emails = list(db.keys())

    # Start Google queries on emails in database
    # populate_database(db, write=True)
