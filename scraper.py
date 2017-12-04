import click
import ingest
import parse
import os

@click.group()
def cli():
    pass


@click.command()
@click.option('--test', default=False, help='testing mode (small database)', is_flag=True)
def make_new_database(test):
    """Read emails from .csv, create empty database and store to disk

    Read emails from input .csv, create empty database and store to disk.
    """
    db = ingest.make_new_database()

    if (test):
        # Testing: try first 10 emails and overwrite the database
        db = {e: db[e] for e in list(db.keys())[1:5]}

    ingest.write_database(db)


@click.command()
@click.option('--query', default='name+surname+email',
    type=click.Choice(['email', 'name+surname+email']),
    help='Google query to use')
@click.option('--write', default=True, help='update database at each query')
def populate_database(query, write):
    """Populate the database by making Google queries. Details are not filled yet.
    """
    db = ingest.load_database()
    db = ingest.populate_database(db, query=query, write=write)


@click.command()
def stats():
    """Show statistics from the saved database."""
    db = ingest.load_database()
    ingest.database_stats(db)


@click.command()
@click.option('--policy', default='first',
    type=click.Choice(['first', 'advanced']),
    help='policy to extract information')
def parse_information(policy):
    """Extract information from Google results in the database."""
    """
    Load the database with stored Google results.
    Parse each result and instantiate corresponding objects.
    Export at the end.
    """

    db = ingest.load_database()
    parse.parseResults(db, policy)


@click.command()
def drop_database():
    """Clear the database from disk."""
    os.remove('database.pickle')


cli.add_command(make_new_database)
cli.add_command(populate_database)
cli.add_command(stats)
cli.add_command(parse_information)
cli.add_command(drop_database)


if __name__ == '__main__':
    cli()
