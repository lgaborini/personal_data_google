import pandas as pd
import pickle
import sys
import subprocess

from google_query import *
import urllib
import urllib.error


def read_addresses():
    df = pd.read_csv('addresses.csv', sep=';', na_filter=False)
    return df


def refresh_VPN():
    print('Refreshing VPN!')
    path = r"C:\Program Files\CyberGhost 6\CyberGhost.exe"

    print('Disconnecting...')
    subprocess.run([path, "/disconnect"], check=False)

    # print('Reconnecting...')
    # res = subprocess.run([path, "/connect"], check=False)
    # print('done.')
    # return True


def write_database(db):
    with open('database.pickle', 'wb') as f:
        pickle.dump(db, f)
    print("Wrote to disk.")


def make_new_database():
    # Make empty db from emails
    df = read_addresses()
    db = dict.fromkeys(df['EmailAddress'].values)
    print("Made new database.")
    return db


def load_database(path='database.pickle'):
    with open(path, 'rb') as f:
        db = pickle.load(f)
    print("Loaded database: {0} entries".format(len(db)))
    return db


def populate_database(db, write=True):
    emails = list(db.keys())

    for i, email in enumerate(emails):

        if not isinstance(email, str):
            continue

        if db[email] is not None:
            # print('Email {0} already known.'.format(email))
            continue

        try:
            print('Querying email {0} ({1}/{2})'.format(email, i, len(emails)))
            result = do_query(email)

            print("Got {0} results.".format(len(result)))
            db[email] = result

            # Update directly
            if write:
                write_database(db)

        except urllib.error.HTTPError as e:
            print('Caught HTTP error: {0}'.format(e))

            if e.code == 503:
                refresh_VPN()
                sys.exit(-1)


def database_stats(db):
    emails = list(db.keys())

    non_null = 0
    for i, email in enumerate(emails):
        if db[email] is not None:
            non_null += 1

    print("Total entries: {0}".format(len(db)))
    print("Non-null entries: {0}".format(non_null))


if __name__ == '__main__':
    # db = make_new_database()
    # write_database(db)

    db = load_database()
    database_stats(db)

    emails = list(db.keys())

    populate_database(db, True)
