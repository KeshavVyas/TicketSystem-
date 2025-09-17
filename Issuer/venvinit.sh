#!/usr/bin/env sh
# Must be run with `source` for activation to occur
if [[ ! -d evn ]]; then
    python3 -m venv env
fi

source env/bin/activate

# to update requirements.txt run `pip freeze > requirements.txt`
pip install -r requirements.txt