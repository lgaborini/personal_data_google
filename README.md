# personal_data_google
Simple script to scrape personal data (websites) from Google results.

Google results are obtained by querying Google with a list of first/last names, company names and email addresses.

# Requirements

Python 3:   
pandas, pickle, subprocess, re, tldextract

The project also imports [Google-Search-API](https://github.com/abenassi/Google-Search-API) (currently by copying, since the code had to be modified).

# Project structure

The project is structured in two parts:
- `ingest.py` reads a structured csv (`addresses.csv`) containing information to build Google queries, and performs Google searches.
- `parse.py` refines saved Google searches, extracts required information and saves to disk (`results.csv`).

## Structure of `ingest.py`:

The script reads an input `csv` file with the following format: 
> Country;CompanyName;FirstName;LastName;Title;EmailAddress
> Germany;Company1;first_name_1;last_name_1;Dr.;foo1@bar.com
> Italy;Company1;first_name_2;last_name_2;Dr.;foo2@bar.com
> Switzerland;Company2;first_name_3;last_name_3;Mr.;foo3@bar.com
> France;Company2;first_name_4;last_name_4;Dr.;foo4@bar.com
> ...

An empty database is created and saved to disk as `database.pickle`.   
A database is a `Dict`, with an email as the key, and a list of `GoogleResults` as values (empty at start).

The datbase is then populated by performing Google searches.   
Currently, the code only parses the first Google result page.

For every entry in the database, a Google query is performed, either by "email" or "firstname lastname email". 
Each result is a list of `GoogleResult` objects, which is associated to the value of the Dictionary.   

The entire database is saved to disk overwriting the previous version.

## Structure of `parse.py`:

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

However, the class is abstract.    
The parsing according to the website type is implemented by derived classes, which overload the validation method.
Inheritance takes care for the dispatch.

