# Copyright Registrations and Renewals DB Maintenance Script

## Introduction

This script creates and updates a database of copyright records, both original registrations and renewals, drawn from two projects supported by the NYPL to digitize and gather this source data. The goal of this project is to create a single source for all copyright information for works registered after 1922 and renewed before 1978 (see [Duration of Copyright](https://www.copyright.gov/circs/circ15a.pdf) for more information). This should provide the connections between registrations and renewals and allow users to see the connections between related registrations and renewals.

The two projects that this data is drawn from are hosted on GitHub, more information about the source of data for these projects can be found in each repository:

- (Catalog of Copyright Entries)[https://github.com/NYPL/catalog_of_copyright_entries_project]
- (Catalog of Copyright Entries Renewals)[https://github.com/NYPL/cce-renewals]

This repository also includes an API for querying the created database using ElasticSearch as a search layer and `Flask` as the application framework. See below for more detail on running and using the search API.

## Database

This script generates and updates a Postgresql database and ElasticSearch search layer. It scans the above repository for updated source files and inserts/updates the appropriate records, ensuring that the search layer is kept up to date following these changes.

### Structure

The database is relatively simple but contains some complexities to describe the range of conditions that exist in the copyright data. The tables currently are:

- `cce` The core table that contains one copyright entry per row, identified by a UUIDv4. This includes a title and other descriptive information
- `renewal` The core table that contains one copyright renewal per row, identified by a UUIDv4 and a renewal number.
- `registration` This table contains copyright registration numbers (e.g. `A999999`) and registration dates. There can be multiple registration numbers per entry and renewal.
- `volume` Contains information describing the CCE volume that specific records were drawn from, including a URL where a digitized version of the volume can be found. This can be used to locate the original text of a copyright entry.
- `author` The authors associated with a copyright entry. For each entry one author is designated as the `primary` author, generally drawn from the entry heading and used for lookup and sorting purposes
- `publisher` The publishers associated with a copyright entry. Each entry is tagged with a boolean `claimant` field that designates if the publisher was the copyright claimant. These entries can overlap with the `author` table due to discrepancies in how data was entered.
- `lccn` Normalized LCCN numbers associated with a copyright entry
- `renewal_claimant` Claimants who have created a renewal record
- `xml` The source XML string for copyright entries. This is stored in an XML field and can be queried with `xpath`. This table also stores successive versions of the source XML for each entry, allowing changes to be found./visualized.
- `error_cce` Contains copyright entries that could not be properly parsed. These are stored to see if the issue lies in the parser or the source data.

### Relationships

The primary relationships are between the `registration` table, entries and renewals. Through registration numbers and dates, connections can be found between entries and renewals. It should be noted that an individual entry can have multiple renewals and vice-versa, related through multiple registration numbers

## ElasticSearch

The ElasticSearch instance is designed to provide a simple, lightweight search layer. The documents in the ElasticSearch do not contain a full set of metadata, simply enough to return results that can be fully realized with an additional query to the database.

The ES instance is comprised of two indexes. `cce` for entries and `ccr` for renewals. These indexes can be queried separately or together

## Configuration

This script can be configured to run locally using the NYPL data sources or your own forks of these sources. A `config.yaml-dist` file is included here that contains the structure for the necessary environment variables. The following will need to be supplied:
- Connection details for a PostgreSQL database
- Connection details for an ElasticSearch instance
- A GitHub Personal Access Token for interacting with the GitHub API
- Repository names for the entry and renewal repositories

## Setup

This script requires Python 3.6+

To create a local instance it is recommended to create a virtualenv and install dependencies with `pip install -r requirements.txt`

## Running

The utility script can be invoked simply with `python main.py` to initialize the database and pull down the full set of source data. Please note that this will take 2-4 hours to fully download, parse and index the source data.

Several command-line arguments control the options for the execution of this script

- `--REINITIALIZE` Will drop the existing database and rebuild it from scratch. WARNING THIS WILL DELETE ALL CURRENT DATA
- `-t` or `--time` The time ago in seconds to check for updated records in the GitHub repositories. This allows for only updating changed records
- `-y` or `--year` A specific year to load from either the entries or renewals
- `-x` or `--exclude` Set to exclude either the entries (with `cce`) or the renewals (with `ccr`) from the current execution. Useful when used in conjunction with the `year` parameter to control what records are updated.

## API

This is a basic API that allows for a limited set of queries to be executed against the database. It allows for lookups by fulltext search, registration/renewal numbers and internal UUID numbers (to retrieve specific records). The returned objects show relationships between registrations and renewals and can optionally return the source data from which each record was created.

### Running the API

To start the api, ensure that that you've updated your `virtualenv` with the most recent version of the requirements file and run the following commands:

1) `export FLASK_ENV=development`
2) `export FLASK_APP=api/app.py`
3) `python -m flask run`

This will start the flask application at `localhost:5000`. Accessing that page will redirect you to a SwaggerDocs page that describes the available endpoints, their parameters, response object and allow users a chance to experiment with the endpoints.

### Using the API

The API provides 5 endpoints for retrieving registration and renewal records. These are split between `Search` and `Lookup` endpoints

#### Search

The search endpoints return many or no object depending on what search terms are used. All three search endpoints share 3 query parameters:

- `page`: The page of results to return. Defaults to 0
- `per_page`: The number of results to return per page. Defaults to 10
- `source`: A flag to set the return of the source XML/CSV data. Defaults to `false`

The individual endpoints are:

- `/search/fulltext?query=<query string>`: A full text query
- `/search/registration/<regnum>`: A search for a specific registration number
- `/search/renewal/<rennum>`: A search for a specific renewal number

#### Lookup

The lookup endpoints return data for a specific Registration or Renewal record. These do not accept additional parameters, but return the `source` data for any record. These endpoints use the internally generated `UUID` numbers to ensure a globally unique lookup value

- `/registration/<uuid>`: Returns a single Registration record
- `/renewal/<uuid>`: Returns a single Renewal record
