# personal_data_google
Simple script to scrape personal data (websites) from Google results.

Google results are obtained by querying Google with a list of first/last names, company names and email addresses.

# Requirements

Python 3:   
pandas, pickle, subprocess, re, tldextract

The project also imports [Google-Search-API](https://github.com/abenassi/Google-Search-API) (currently by copying, since the code had to be modified).

# Usage

The script is designed to be run by providing a suitable `addresses.csv`.

## Usage (CLI):

The file [scraper.py](./scraper.py) provides a small command-line access to the scraper.

Any command is specified as follows:

> python scraper.py [command]

Documentation for each command is provided with the flag `--help`:

> python scraper.py [command] --help

### Available commands:
- `make_new_database` create empty database from file `addresses.csv`
- `drop_database` clear the database
- `stats` show some statistics on the stored database
- `populate_database` perform Google queries and save to disk
- `parse_information` extract information from Google queries and save to `results.csv`

### Example session:

> python scraper.py make_database
> python scraper.py stats
> python scraper.py populate_database --query name+surname+email
> python scraper.py parse_information --policy advanced
> 


## Usage (manual):

The older way.

### First run:
the database must be created and saved by uncommenting the following line in [ingest.py](./ingest.py):
> db = make_new_database()

and running:
> python ingest.py   
> python parse.py

#### Subsequent runs:
the database is update only if necessary; elements with stored `GoogleResults` will not be modified.
> python parse.py

### Options

The type of Google query can also be modified by passing the appropriate parameter to function `populate_database`.

Once all requests have been performed, [parse.py](./parse.py) takes care of extracting information.
The choice of parser method is performed in the `main` function.


# Project structure

The project is structured in two parts:
- [ingest.py](./ingest.py) reads a structured csv (`addresses.csv`) containing information to build Google queries, and performs Google searches.
- [parse.py](./parse.py) refines saved Google searches, extracts required information and saves to disk (`results.csv`).
- [scraper.py](./scraper.py) contains the CLI interface


## Structure of [ingest.py](./ingest.py):

The script reads an input `csv` file with the following format: 
> Country;CompanyName;FirstName;LastName;Title;EmailAddress
> Germany;Company1;first_name_1;last_name_1;Dr.;foo1@bar.com
> Italy;Company1;first_name_2;last_name_2;Dr.;foo2@bar.com
> Switzerland;Company2;first_name_3;last_name_3;Mr.;foo3@bar.com
> France;Company2;first_name_4;last_name_4;Dr.;foo4@bar.com    
> ...

Required fields are:
- `Country`
- `CompanyName`
- `FirstName`
- `LastName`
- `Title`
- `EmailAddress`

An empty database is created and saved to disk as `database.pickle`.   
A database is a `Dict`, with an email as the key, and a list of `GoogleResults` as values (empty at start).

The database is then populated by performing Google searches.   
Currently, the code only parses the first Google result page.

For every entry in the database, a Google query is performed, either by "email" or "firstname lastname email". 
Each result is a list of `GoogleResult` objects, which is associated to the value of the Dictionary.   

The entire database is saved to disk overwriting the previous version.   
Feel free to interrupt the script anytime, as the database is saved at each row.   
People with GoogleResults will not be checked again.   

## Structure of [parse.py](./parse.py):

This script re-reads the saved database, and extract information for every individual according to the obtained Google results.

The output of the main parsing function is a dictionary containing query data (first name, last name, email, ...) and the extracted information for each individual.   

It does so in two ways:
- either the first Google result is selected (`parseFirstResult`), or
- an heuristic parser analyzes all results, returning the most promising ones (`parseAdvanced`)

The output dictionary is then saved to disk as `results.csv`, with the corresponding extracted columns.

### Heuristic parser

To each individual, we associate a set of objects which are populated with the list of searches.   
In detail, the code seeks to extract a personal LinkedIn page, the ResearchGate profile, or a generic personal page (e.g. research institute website).   
To do so, it makes use of lots of heuristics (to be continuously updated and improved).

The main class representing personal information is `PersonInformationResult`.   
This class is mainly tied to the person (his email) and to a type of website (currently either `LinkedIn`, `ResearchGate`, `personal page`).   
It holds the most promising result, as well as other Google results which may contain useful data as well ("candidates").

The main workhorse is the function `validate_result`.    
`validate_result` returns `True` if the given page contains information.
The method `populateFromGoogleResults` validates every result for an individual, and fills information for `PersonInformationResult`.   
Currently, only the result link is retained, no further parsing is performed on the page.

However, the class `PersonInformationResult` is abstract.    
The parsing according to the website type is implemented by derived classes, which overload the validation method.
Inheritance dispatches the call of `validate_result` to the correct class.

### Caution
The script reads and performs Google searches on the specified data.
Notice that Google throttles requests, and an exception is thrown when the maximum amount of requests is reached.

## Disclaimer

This script has been written only for learning purposes. No other use is authorized.

## TODO:

- [x] Implement command-line options
- [ ] Insert script to activate/deactivate VPN when necessary
- [ ] Display data on a Flask app
- [ ] Fix dependency on Google-Search-API

