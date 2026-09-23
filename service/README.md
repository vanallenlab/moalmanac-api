Scripts in this directory are used to serve the application on a Google Compute Engine VM.

## Installation

1. Create VM. Used e2-small with ubuntu-22.04 LTS
2. Create a static ip address to associate with the VM
3. Add A and CNAME to zone under network services > cloud dns > and your zone, if you haven't already created one
4. Launch VM, pull repo with GitHub and git token
5. Run `git submodule update --init --recursive` to check out the `moalmanac-db` submodule. The application imports `moalmanac-db/utils/dereference.py` directly at every startup to build the dereferenced record cache it serves, so it will fail to start without the submodule checked out.
6. Run `copy_serving_files_and_start_service.sh` to configure gunicorn and nginx.
7. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate. This is done through certbot.
8. Run `secure-application.sh` to install https certifications

## View logs

- `project-view-log.sh` to view the system log for project
- `nginx-view.sh` to view nginx process logs
- `nginx-view-access.sh` to view nginx access logs
- `nginx-view-error.sh` to view nginx error logs

Add A and CNAME to zone under network services.
