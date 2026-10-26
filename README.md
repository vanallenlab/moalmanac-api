[![License: CC BY 4.0](https://img.shields.io/badge/Database-CC%20BY%204.0-informational)](./LICENSE)
[![License: GPL v2](https://img.shields.io/badge/Code-GPL%20v2-informational)](./LICENSE-code)

Application Program Interface (API) for the [Molecular Oncology Almanac's knowledge base](https://github.com/vanallenlab/moalmanac-db) and [browser](https://github.com/vanallenlab/moalmanac-browser/tree/main), available at: [https://api.moalmanac.org](https://api.moalmanac.org).

## Installation

### Download

This repository can be downloaded through GitHub by either using the website or terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP` to download this repository in a compressed format. To install using GitHub on terminal, type:

```bash
git clone https://github.com/vanallenlab/moalmanac-api.git --recurse-submodules
cd moalmanac-api
```

This repository includes [moalmanac-db](https://github.com/vanallenlab/moalmanac-db) as a [submodule](https://github.blog/open-source/git/working-with-submodules/). You can update moalmanac-db to the latest commit:

```bash
git submodule update --init --recursive
```

To update moalmanac-db to the latest commit, use [update_submodule_to_commit.sh](update_submodule_to_commit.sh):

```bash
bash update_submodule_to_commit.sh
```

Alternatively, to update moalmanac-db to a specific commit:

```bash
bash update_submodule_to_commit.sh <commit hash>
```

The script also regenerates [docs/openapi.json](docs/openapi.json) (see [OpenAPI schema](#openapi-schema)) and commits it together with the submodule update, so run it with this repository's Python environment activated, or point `PYTHON` at it (e.g. `PYTHON=/path/to/python bash update_submodule_to_commit.sh`). It refuses to run while `app/` has uncommitted changes, so the committed schema matches the committed code, and it commits nothing if regenerating the schema fails.

### Python dependencies

This repository uses Python 3.12. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or [Miniconda](https://conda.io/miniconda.html).

Run the following from this repository's directory to create a virtual environment and install dependencies with Anaconda or Miniconda:

```bash
conda create -y -n moalmanac-api python=3.12
conda activate moalmanac-api
pip install -r requirements.txt
```

Or, if using base Python:

```bash
virtualenv venv
source activate venv/bin/activate
pip install -r requirements.txt
```

To make the virtual environment available to jupyter notebooks, execute the following code while the virtual environment is activated:

```bash
pip install jupyter
ipython kernel install --user --name=moalmanac-api
```

## Usage

To update the database content from [moalmanac-db](https://github.com/vanallenlab/moalmanac-db):

 ```bash
rm data/moalmanac.sqlite3; python -m app.populate_database -i moalmanac_db/referenced/ -c config.ini
```

### Environment configuration

Configuration variables are managed using environment files:

- [.env](.env) - used for local development
- [.env.production](.env.production) - used for production, loaded with systemd

To launch the application for development, using variables from [.env](.env):

```bash
python run.py
```

### Production deployment

The API is hosted on the same VM as every [moalmanac-browser](https://github.com/vanallenlab/moalmanac-browser) instance, behind one nginx. Gunicorn listens on `127.0.0.1:8000`, which nginx proxies to for `api.moalmanac.org` and which browser instances use directly. See [service/README.md](service/README.md) for set up.

This repository uses [Gunicorn](https://gunicorn.org) with Uvicorn workers to serve the FastAPI application for production. The service is configured using a [systemd unit file, service/moalmanac-api.service](service/moalmanac-api.service), which sets environment variables from [.env.production](.env.production) via the `EnvironmentFile` variable:

```ini
EnvironmentFile=/srv/moalmanac/moalmanac-api/.env.production
```

Gunicorn is launched using the provided `ExecStart` command:

```ini
/srv/moalmanac/miniforge3/envs/moalmanac-api/bin/gunicorn --workers ${GUNICORN_WORKERS} --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 app.main:app
```

Systemd and Gunicorn manage launching the application for production using the [service/moalmanac-api.service](service/moalmanac-api.service) file, so there is no need to run `python run.py` for production use.

## Development

### OpenAPI schema

The API's interactive documentation is served at [https://api.moalmanac.org](https://api.moalmanac.org). A copy of its OpenAPI schema is committed at [docs/openapi.json](docs/openapi.json), which the [documentation site](https://docs.moalmanac.org) renders. Response schemas and examples in it are built from moalmanac-db's JSON Schemas and records (see [app/schemas.py](app/schemas.py)).

Regenerate it whenever [app/routers/main/routes.py](./app/routers/main/routes.py) changes (routes, their parameters, or docstrings) or moalmanac-db is updated, and commit it with the change:

```bash
python utils/export_openapi.py
```

[update_submodule_to_commit.sh](update_submodule_to_commit.sh) does this automatically when updating moalmanac-db.

### Continuous integration

[GitHub Actions](.github/workflows/ci.yml) runs on every pull request and every push to `main`:

- `ruff check app utils tests run.py`
- `python utils/export_openapi.py --check`, which fails if [docs/openapi.json](docs/openapi.json) is out of date
- `python -m pytest`

To run the same checks locally before pushing:

```bash
ruff check app utils tests run.py
python utils/export_openapi.py --check
python -m pytest
```

## Citation

If you find this tool or any code herein useful, please cite:
> [Reardon, B., Moore, N.D., Moore, N.S., *et al*. Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology. *Nat Cancer* (2021). https://doi.org/10.1038/s43018-021-00243-3](https://www.nature.com/articles/s43018-021-00243-3)

## License

- Database content: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), see [LICENSE](./LICENSE).
- Code: [GNU General Public License, Version 2 (GPL v2)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html), see [LICENSE-code.md](./LICENSE-code.md).

## Disclaimer

For purposes of this Disclaimer, the “Service” means the Molecular Oncology Almanac database, software, API, browsers, and related materials.

THIS DATABASE AND SOFTWARE HAVE NOT BEEN VALIDATED FOR DIAGNOSTIC OR CLINICAL USE, AND DANA-FARBER CANCER INSTITUTE (DFCI) MAKES NO WARRANTY OF FITNESS FOR DIAGNOSTIC OR CLINICAL USE. USERS ARE SOLELY RESPONSIBLE FOR ENSURING THAT THEIR ACCESS TO AND USE OF THE DATABASE, SOFTWARE, API, BROWSERS, AND RELATED MATERIALS COMPLIES WITH ALL APPLICABLE LAWS, REGULATIONS, INSTITUTIONAL POLICIES, AND ETHICAL REQUIREMENTS, INCLUDING ANY REQUIREMENTS APPLICABLE TO RESEARCH INVOLVING HUMAN SUBJECTS OR HUMAN-DERIVED DATA. DFCI MAKES NO REPRESENTATIONS OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT OR VALIDITY OF ANY INTELLECTUAL PROPERTY RIGHTS OR CLAIMS, WHETHER ISSUED OR PENDING, AND THE ABSENCE OF LATENT OR OTHER DEFECTS, WHETHER OR NOT DISCOVERABLE.

In no event shall DFCI or its trustees, directors, officers, employees, students, affiliates, core faculty, associate faculty and contractors be liable for incidental, punitive, consequential or special damages, including economic damages or injury to persons or property or lost profits, regardless of whether the party was advised, had other reason to know or in fact knew of the possibility of the foregoing, regardless of fault, and regardless of legal theory or basis. To the extent liability cannot be disclaimed, DFCI’s liability shall be limited to direct, actual damages resulting from DFCI’s failure to perform its obligations under the applicable terms.
