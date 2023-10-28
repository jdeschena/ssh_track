# ssh_track

Small util script to automatically replicate a local directory on a remote machine. Replacement for VSCode ssh remote work (slow) or PyCharm automatic deploy (paid), in a simple python file.


## Install
```bash
git clone git@github.com:deschena/ssh_track.git
cd ssh_track
pip install .
```

## Arguments
```bash
usage: ssh_track [-h] [--config_path CONFIG_PATH] [--local_dir LOCAL_DIR] [--remote_dir REMOTE_DIR] [--hostname HOSTNAME] [--port PORT]
                 [--username USERNAME] [--pkey_path PKEY_PATH] [--display_last_k DISPLAY_LAST_K]

options:
  -h, --help            show this help message and exit
  --config_path CONFIG_PATH
                        Path to an optional config to override the cli args.
  --local_dir LOCAL_DIR
                        Local directory to track (absolute, recursive).
  --remote_dir REMOTE_DIR
                        Remote directory to copy to (absolute).
  --hostname HOSTNAME   host to ssh into.
  --port PORT           port to use for ssh connection. Default: 22
  --username USERNAME   Username on remote machine.
  --pkey_path PKEY_PATH
                        Local path of the private Ed25519 key to use (absolute).
  --display_last_k DISPLAY_LAST_K
                        Max number of event to display. Default: 25
```

## Examples

### Command line only
```bash
ssh_track --local_dir /User/me/documents/fancy_project --remote_dir /home/me/fancy_project --hostname my.remote.server.com --username me --pkey_path /Users/me/.ssh/my_key
```

### Using a config
```bash
ssh_track --config_path config.yaml
```

The config:
```yaml
local_dir: /User/me/documents/fancy_project
remote_dir: /home/me/fancy_project
hostname: my.remote.server.com
port: 22
username: me
pkey_path: /Users/me/.ssh/my_key
display_last_k: 30

```
