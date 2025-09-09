# SpyPlane

Scouting bot

# Functional Notes

[Link to Notes](https://docs.google.com/document/d/1a4U9vYSLk9_sQVjA3xz49KnCS0hibOq2ELEXc87X9yI/edit?usp=sharing)

# Tech Notes

## Local devbox setup

1. Install [uv using instructions here](https://github.com/astral-sh/uv#installation)
2. Create a virtual environment: `uv venv`
3. Activate the virtual environment: `source .venv/bin/activate`
4. Install dependencies: `uv pip sync requirements.lock`
5. Copy `.env.sample` to `.env` and update the values for TEST and PROD
6. Contact the dev team to get the token.json that allows connecting to Google Sheets API,
and place it in the repo root.
7. Startup the bot with `python -m spyplane.main`

## Google Drive Setup

Follow [gspread instructions](https://docs.gspread.org/en/latest/oauth2.html)
to connect to google sheet from your drive

## Running tests

From the repo root

```bash
python -m unittest
```


