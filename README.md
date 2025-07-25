# Molecular Oncology Almanac API
API for the [moalmanac-db](https://github.com/vanallenlab/moalmanac-db) and [moalmanac-browser](https://github.com/vanallenlab/moalmanac-browser/tree/main). Available at [https://api.moalmanac.org](https://api.moalmanac.org).

## Installation 
### Download
This repository can be downloaded through GitHub by either using the website or terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP` to download this repository in a compressed format. To install using GitHub on terminal, type:
```bash
git clone https://github.com/vanallenlab/moalmanac-api.git --recursive-submodules
cd moalmanac-api
```
This repository includes [moalmanac-db](https://github.com/vanallenlab/moalmanac-db) as a [submodule](https://github.blog/open-source/git/working-with-submodules/). You can update moalmanac-db to the latest commit: 
```bash
git submodule update --init --recursive
```

To update moalmanac-db to the latest commit, use [update_submodule_to_commit.sh](update_submodule_to_commit.sh):
```bash
bash update_submodule_to_commit 
```

Alternatively, to update moalmanac-db to a specific commit:
```bash
bash update_submodule_to_commit <commit hash>
```

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
rm data/moalmanac.sqlite3; python -m app.populate_database -i moalmanac-db/referenced/ -c config.ini
```

### Environment configuration
Flask configuration variables are managed using environment files:

- [.env](.env) - used for local development
- [.env.production](.env.production) - used for production, loaded with systemd 

To launch the application for development, using variables from [.env](.env):
```bash
python run.py
```

### Production deployment
This repository uses [Gunicorn](https://gunicorn.org) to serve the Flask application for production. The service is configured using a [systemd unit file, service/moalmanac-api.service](service/moalmanac-api.service), which sets environment variables from [.env.production](.env.production) via the `EnvironmentFile` variable:
```ini
EnvironmentFile=/home/breardon/moalmanac-api/.env.production
```
Gunicorn is launched using the provided `ExecStart` command:
```ini
/home/breardon/mambaforge-pypy3/envs/moalmanac-api/bin/gunicorn --workers 5 --bind unix:moalmanac-api.sock -m 007 run:app
```
Systemd and Gunicorn manage launching the application for production using the [service/moalmanac-api.service](service/moalmanac-api.service) file, so there is no need to run `python run.py` for production use.

## Citation
If you find this tool or any code herein useful, please cite:  
> [Reardon, B., Moore, N.D., Moore, N.S., *et al*. Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology. *Nat Cancer* (2021). https://doi.org/10.1038/s43018-021-00243-3](https://www.nature.com/articles/s43018-021-00243-3)

## Disclaimer - For research use only
DIAGNOSTIC AND CLINICAL USE PROHIBITED. DANA-FARBER CANCER INSTITUTE (DFCI) and THE BROAD INSTITUTE (Broad) MAKE NO REPRESENTATIONS OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT OR VALIDITY OF ANY INTELLECTUAL PROPERTY RIGHTS OR CLAIMS, WHETHER ISSUED OR PENDING, AND THE ABSENCE OF LATENT OR OTHER DEFECTS, WHETHER OR NOT DISCOVERABLE.

In no event shall DFCI or Broad or their Trustees, Directors, Officers, Employees, Students, Affiliates, Core Faculty, Associate Faculty and Contractors, be liable for incidental, punitive, consequential or special damages, including economic damages or injury to persons or property or lost profits, regardless of whether the party was advised, had other reason to know or in fact knew of the possibility of the foregoing, regardless of fault, and regardless of legal theory or basis. You may not download or use any portion of this program for any non-research use not expressly authorized by DFCI or Broad. You further agree that the program shall not be used as the basis of a commercial product and that the program shall not be rewritten or otherwise adapted to circumvent the need for obtaining permission for use of the program other than as specified herein.
