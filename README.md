## First do this

1. Create and activate a venv:
```bash
$ python -m venv venv
$ source venv/bin/activate 
``` 
2. Install packages. If you dont have access to pypi.lime.tech in the venv install limepkg-metabase first:
```bash
$ pip install limepkg-metabase==1.4.0.dev2 --index-url https://pypi.lime.tech/simple/
$ pip install -r requirements.txt
```
3. Get an `.env` from Roger.

## How to run export test

To create a file with appliction data that can be used for testing export do:

```bash
$ python main.py load-applications -e <ENVIRONMENT>
```

`ENVIRONMENT` can be either `testing` or `production`. Applications will be stored in a file called `application-<ENVIRONMENT>.json`.

To run the export command use

```bash
$ python main.py test-export -e <ENVIRONMENT>
```

This will loop over all applications in the `application-<ENVIRONMENT>.json` and invoke the export API in limepkg-metabase. 

The result of the export will be saved as `export_status` for each application in the file.

If there is already an export_status, the app is ignored the next time an export is performed. If you want to run it again, you need to remove the "export_status" line.

