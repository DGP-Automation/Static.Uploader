# Static.Uploader
 
A simple tool to upload files to the Alist server.

## Available options:
`--type`: `zip`, `raw`, `generic`
`--file`: local file path to upload
`--target`: remote file path
`--host`: alist server host, or set it in system environment
`--username`: alist server username, or set it in system environment
`--password`: alist server password, or set it in system environment
`--overwrite`: overwrite remote file if exists

---

For Snap.Static repository, use `--type zip` or `--type raw` and set env in GitHub Actions is enough.

For other files, use `--type generic` and fill other options.

e.g. `--type generic --file output/Snap.Hutao.Deployment.exe --target /tools --host d.hut.ao --username snaphutao
--pasword snaphutaopassword --overwrite`