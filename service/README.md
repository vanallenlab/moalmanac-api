Scripts in this directory are used to serve the application on a Google Compute Engine VM.

The VM is shared with every [moalmanac-browser](https://github.com/vanallenlab/moalmanac-browser) instance behind a single nginx. The API listens on `127.0.0.1:8000`: nginx proxies `api.moalmanac.org` to it, and browser instances on the same VM request data from it directly rather than over the internet. Set up the API first, then follow moalmanac-browser's [service/README.md](https://github.com/vanallenlab/moalmanac-browser/blob/main/service/README.md) for the browser instances.

## Installation

1. Create VM. We recommend e2-standard-4 (4 vCPU, 16 GB) with ubuntu-22.04 LTS, as it hosts the API and all browser instances.
2. Create a static ip address to associate with the VM
3. Add A and CNAME to zone under network services > cloud dns > and your zone, if you haven't already created one
4. Launch VM, pull repo with GitHub and git token
5. Run `git submodule update --init --recursive` to check out the `moalmanac-db` submodule. The application imports `moalmanac-db/utils/dereference.py` directly at every startup to build the dereferenced record cache it serves, so it will fail to start without the submodule checked out.
6. Run `copy_serving_files_and_start_service.sh` to configure gunicorn and nginx. Confirm the API responds with `curl http://127.0.0.1:8000/`.
7. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate. This is done through certbot.
8. Run `secure-application.sh` to install https certifications

Gunicorn worker count is set by `GUNICORN_WORKERS` in [.env.production](../.env.production). Each worker holds its own copy of the dereferenced record cache in memory, so check memory use with `ps -o rss,cmd -C gunicorn` before raising it.

## View logs

- `project-view-log.sh` to view the system log for project
- `nginx-view.sh` to view nginx process logs
- `nginx-view-access-log.sh` to view nginx access logs
- `nginx-view-error-log.sh` to view nginx error logs

Add A and CNAME to zone under network services.
