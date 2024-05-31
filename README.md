# Page analyzer

## Hexlet tests and linter status

[![Actions Status](https://github.com/fiftinmen/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/fiftinmen/python-project-83/actions)

## Code climate maintainability status

[![Maintainability](https://api.codeclimate.com/v1/badges/fd3b4c86fa592d6e9c17/maintainability)](https://codeclimate.com/github/fiftinmen/python-project-83/maintainability)

## Description

Simple tool for page SEO-analyzing.

## Prerequisites

To successfully install you need:

1. git,
2. python 3.10 (not tested with other versions),
3. poetry 1.3.1 or higher ,
4. postgresql 16 (not tested with other versions).

## Installation

1. Clone repository:
`git clone https://github.com/fiftinmen/python-project-83`
2. Create database.
3. Create environment variable with URL containing path to database, username and user's password. Save it into file in root directory of project in ".env" file.
4. Install dependencies with poetry:
`poetry install`

## Usage

1. Run server:
`make start`
You'll see something like that:
`
...
[2024-05-30 21:14:32 +0300] [23556] [INFO] Listening at: http://0.0.0.0:8000 (23556)
...
`
2. Follow the URL above.
3. Enter an URL in the input field.
4. Once you'l provide valid URL you'll be redirected to page_checker,
5. Press "Запустить проверку" button.
