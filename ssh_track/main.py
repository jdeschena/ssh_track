import os
from os import path as osp
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.style import Style
from datetime import datetime
import argparse
import yaml
from omegaconf import OmegaConf


def main():
    parser = argparse.ArgumentParser(add_help=True)
    add_arguments(parser)
    args = parser.parse_args()
    args = OmegaConf.create(vars(args))

    if args.config_path is not None:
        with open(args.config_path, "r") as f:
            cfg = yaml.safe_load(f)
            args = OmegaConf.create(cfg)

    event_handler = UploadHandler(
        args.local_dir,
        args.remote_dir,
        args.hostname,
        args.port,
        args.username,
        args.pkey_path,
        args.display_last_k,
    )
    observer = Observer()
    observer.schedule(event_handler, path=args.local_dir, recursive=True)
    observer.start()
    observer.join()


def add_arguments(parser):
    parser.add_argument(
        "--config_path",
        type=str,
        help="Path to an optional config to override the cli args.",
    )
    parser.add_argument(
        "--local_dir", type=str, help="Local directory to track (absolute, recursive)."
    )
    parser.add_argument(
        "--remote_dir", type=str, help="Remote directory to copy to (absolute)."
    )
    parser.add_argument("--hostname", type=str, help="host to ssh into.")
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="port to use for ssh connection. Default: 22",
    )
    parser.add_argument("--username", type=str, help="Username on remote machine.")
    parser.add_argument(
        "--pkey_path",
        type=str,
        help="Local path of the private Ed25519 key to use (absolute).",
    )
    parser.add_argument(
        "--display_last_k",
        type=int,
        default=25,
        help="Max number of event to display. Default: 25",
    )


def clear_screen():
    if os.name == "posix":  # For Unix/Linux/Mac
        os.system("clear")
    elif os.name == "nt":  # For Windows
        os.system("cls")


def rec_make_dir(sftp, remote_dirs):
    remote_dirs = remote_dirs.split("/")
    remote_dirs = [x for x in remote_dirs if x != ""]
    for idx in range(1, len(remote_dirs)):
        prefix = remote_dirs[:idx]
        prefix = "/" + osp.join(*prefix)
        try:
            sftp.mkdir(prefix)
        except:
            pass


def _datetime_tuple():
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.strftime("%H:%M:%S")
    return str(current_date), str(current_time)


def _generate_table(last_messages):
    table = Table()
    table.add_column("Date", style="green")
    table.add_column("Time", style="green")
    table.add_column("Action", justify="center", style="cyan")
    table.add_column("Source", style="magenta")

    table.title = "Automatic file upload handler"
    table.title_style = Style(bold=True, color="red")
    table.grid_style = Style(color="blue")

    for row in last_messages:
        table.add_row(*row)

    return table


class UploadHandler(FileSystemEventHandler):
    def __init__(
        self,
        local_directory,
        remote_directory,
        hostname,
        port,
        username,
        private_key_path,
        keep_last_k,
    ):
        super().__init__()
        self.local_directory = local_directory
        self.remote_directory = remote_directory
        self.hostname = hostname
        self.port = port
        self.username = username
        self.private_key_path = private_key_path
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Display stuff
        self.last_messages = []
        self.keep_last_k = keep_last_k

        private_key = paramiko.Ed25519Key(filename=private_key_path)
        self.ssh_client.connect(hostname, port, username, pkey=private_key)
        self.sftp = self.ssh_client.open_sftp()
        self.sftp

        clear_screen()
        self.live = Live(_generate_table(self.last_messages))
        self.console = Console()
        self.update_table()

    def _add_event(self, type, source):
        update = _datetime_tuple()
        update = update + (type, source)
        self.last_messages.append(update)
        self.update_table()

    def update_table(self):
        self.last_messages = self.last_messages[-self.keep_last_k :]
        table = _generate_table(self.last_messages)
        self.console.clear()
        self.console.print(table)

    def destroy(self):
        self.sftp.close()
        self.ssh_client.close()

    def on_modified(self, event):
        if event.is_directory:
            return
        self.upload_file(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            self.delete_remote_dir(event.src_path)
        else:
            self.delete_remote_file(event.src_path)

    def delete_remote_dir(self, src_path):
        remote_dir_path = src_path.replace(self.local_directory, self.remote_directory)

        try:
            self.sftp.rmdir(remote_dir_path)
        except OSError as e:
            pass

        self._add_event("RMDIR", src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self.move_remote_file(event.src_path, event.dest_path)

    def upload_file(self, local_file_path):
        remote_file_path = local_file_path.replace(
            self.local_directory, self.remote_directory
        )
        # Perform actions on the remote machine (e.g., upload the file)
        was_uploaded = False
        while not was_uploaded:
            try:
                self.sftp.put(local_file_path, remote_file_path)
                was_uploaded = True
            except FileNotFoundError:
                # Sometimes OS triggers modify + delete event on delete
                if not osp.exists(local_file_path):
                    was_uploaded = True
                else:
                    rec_make_dir(self.sftp, remote_file_path)
        self._add_event("MV/NEW", local_file_path)

    def delete_remote_file(self, local_file_path):
        remote_file_path = local_file_path.replace(
            self.local_directory, self.remote_directory
        )

        try:
            self.sftp.remove(remote_file_path)
            self._add_event("RM", local_file_path)
        except FileNotFoundError as e:
            self._add_event("ERROR RM", local_file_path)

    def move_remote_file(self, src_local_path, dest_local_path):
        # Define the remote file paths based on the local paths
        src_remote_path = src_local_path.replace(
            self.local_directory, self.remote_directory
        )
        dest_remote_path = dest_local_path.replace(
            self.local_directory, self.remote_directory
        )

        try:
            self.sftp.remove(
                dest_remote_path
            )  # Remove the destination file if it exists
        except FileNotFoundError:
            pass
        self.sftp.rename(src_remote_path, dest_remote_path)
        self._add_event("MOVE", src_local_path)


if __name__ == "__main__":
    main()
