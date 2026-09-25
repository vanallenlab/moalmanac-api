Scripts in this directory are used to serve the application on a Google Compute Engine VM.

The VM is shared with every [moalmanac-browser](https://github.com/vanallenlab/moalmanac-browser) instance behind a single nginx. The API listens on `127.0.0.1:8000`: nginx proxies `api.moalmanac.org` to it, and browser instances on the same VM request data from it directly rather than over the internet. Set up the API first, then follow moalmanac-browser's [service/README.md](https://github.com/vanallenlab/moalmanac-browser/blob/main/service/README.md) for the browser instances.

## Service account

The API and every browser instance run as the `moalmanac` account, not as a person's login. Its home directory, `/srv/moalmanac`, holds the conda install and both repositories:

```text
/srv/moalmanac/
├── miniforge3/            conda, with the moalmanac-api and moalmanac-browser environments
├── moalmanac-api/
└── moalmanac-browser/
```

The account has no password and no SSH keys, so nobody logs in as it directly. Administrators sign in with their own account and switch to it with `sudo -iu moalmanac` for anything that changes these files, such as `git pull` or rebuilding a cache, so ownership stays correct. Commands that need `sudo` (the setup scripts, `systemctl`, `certbot`) are run from the administrator's own account.

Create the account and the conda install once per VM:

```bash
sudo useradd --system --create-home --home-dir /srv/moalmanac --shell /bin/bash moalmanac
sudo -iu moalmanac bash -c '
  curl -L -o Miniforge3-Linux-x86_64.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  bash Miniforge3-Linux-x86_64.sh -b -p /srv/moalmanac/miniforge3 && rm Miniforge3-Linux-x86_64.sh
  /srv/moalmanac/miniforge3/bin/conda init bash
'
```

## Installation

1. Create VM. We recommend e2-standard-4 (4 vCPU, 16 GB) with ubuntu-24.04 LTS, as it hosts the API and all browser instances.
2. Create a static ip address to associate with the VM
3. Add A and CNAME to zone under network services > cloud dns > and your zone, if you haven't already created one
4. Create the `moalmanac` account and its conda install, as described in [Service account](#service-account).
5. As `moalmanac` (`sudo -iu moalmanac`), clone this repository with its `moalmanac-db` submodule and build its environment. The application imports `moalmanac-db/utils/dereference.py` directly at every startup to build the dereferenced record cache it serves, so it will fail to start without the submodule checked out.

   ```bash
   git clone --recurse-submodules https://github.com/vanallenlab/moalmanac-api.git /srv/moalmanac/moalmanac-api
   conda create -y -n moalmanac-api python=3.12
   /srv/moalmanac/miniforge3/envs/moalmanac-api/bin/pip install -r /srv/moalmanac/moalmanac-api/requirements.txt
   ```

6. From your own account, run `copy_serving_files_and_start_service.sh` from `/srv/moalmanac/moalmanac-api/service` to configure gunicorn and nginx. Confirm the API responds with `curl http://127.0.0.1:8000/`.
7. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate. This is done through certbot.
8. Run `secure-application.sh` to install https certifications

Gunicorn worker count is set by `GUNICORN_WORKERS` in [.env.production](../.env.production). Each worker holds its own copy of the dereferenced record cache in memory, so check memory use with `ps -o rss,cmd -C gunicorn` before raising it.

## View logs

- `project-view-log.sh` to view the system log for project
- `nginx-view.sh` to view nginx process logs
- `nginx-view-access-log.sh` to view nginx access logs
- `nginx-view-error-log.sh` to view nginx error logs

Add A and CNAME to zone under network services.
