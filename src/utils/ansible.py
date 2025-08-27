from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pathlib import Path

import yaml


def str_representer(dumper: yaml.Dumper, data: str) -> yaml.nodes.ScalarNode:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)  # type: ignore


yaml.SafeDumper.add_representer(str, str_representer)  # type: ignore

Condition = Union[str, List[str]]

modules = {
    "apt": "ansible.builtin.apt",
    "file": "ansible.builtin.file",
    "git": "ansible.builtin.git",
    "shell": "ansible.builtin.shell",
    "systemd": "ansible.builtin.systemd_service",
    "stat": "ansible.builtin.stat",
    "powershell": "ansible.windows.win_powershell",
    "win_powershell": "ansible.windows.win_powershell",
    "win_shell": "ansible.windows.win_shell",
    "win_copy": "ansible.windows.win_copy",
    "win_file": "ansible.windows.win_file",
}


@dataclass
class Task:
    name: str
    module: str
    args: Dict[str, Any] = field(default_factory=lambda: {})
    register: Optional[str] = None
    when: Optional[Condition] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name, self.module: self.args or {}}
        if self.register:
            d["register"] = self.register
        if self.when:
            d["when"] = self.when
        return d


@dataclass
class Play:
    name: Optional[str] = None
    hosts: Optional[str] = None
    become: bool = False
    tasks: List[Task] = field(default_factory=lambda: [])

    def add_task(
        self,
        task_name: str,
        module: str,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
        **args: Any,
    ) -> "Play":
        self.tasks.append(
            Task(name=task_name, module=module, args=args, register=register, when=when)
        )
        return self

    def stat(self, task_name: str, path: str, register: str) -> "Play":
        return self.add_task(task_name, modules["stat"], register=register, path=path)

    def add_apt(self, task_name: str, pkg: str, **kwargs: Any) -> "Play":
        params = {"name": pkg}
        params.update(kwargs)
        return self.add_task(task_name, modules["apt"], **params)

    def systemd_service(
        self,
        task_name: str,
        **kwargs: Any,
    ):
        return self.add_task(task_name, modules["systemd"], **kwargs)

    def create_directory(
        self,
        task_name: str,
        path: str,
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[str] = None,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
    ) -> "Play":
        args = {"path": path, "state": "directory"}
        if owner:
            args["owner"] = owner
        if group:
            args["group"] = group
        if mode:
            args["mode"] = mode

        return self.add_task(
            task_name, modules["file"], register=register, when=when, **args
        )

    def chown(
        self,
        task_name: str,
        path: str,
        owner: str,
        group: str,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
    ) -> "Play":
        return self.add_task(
            task_name,
            modules["file"],
            register=register,
            when=when,
            path=path,
            owner=owner,
            group=group,
        )

    def mass_clone(
        self,
        base_dest: str,
        repos: List[str],
        register: Optional[str] = None,
        when: Optional[Condition] = None,
    ) -> "Play":
        for repo in repos:
            repo_name = repo.split("/")[-1].replace(".git", "")
            dest = f"{base_dest}/{repo_name}"
            self.git_clone(
                f"Clone {repo_name}",
                repo,
                dest,
                register=register,
                when=when,
            )
        return self

    def wget(
        self,
        task_name: str,
        url: str,
        dest: str,
        owner: Optional[str] = None,
        group: Optional[str] = None,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
    ) -> "Play":
        return self.add_task(
            task_name,
            "ansible.builtin.get_url",
            url=url,
            dest=dest,
            owner=owner if owner else None,
            group=group if group else None,
            register=register,
            when=when,
        )

    def sh(
        self,
        task_name: str,
        cmd: str,
        register: Optional[str] = None,
        when: Optional[str] = None,
    ) -> "Play":

        cmd = cmd.strip()

        return self.add_task(
            task_name,
            modules["shell"],
            cmd=cmd,
            register=register,
            when=when,
        )

    def mass_wget(
        self,
        base_dest: str,
        urls: List[str],
        owner: Optional[str] = None,
        group: Optional[str] = None,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
    ) -> "Play":
        for url in urls:
            file_name = url.split("/")[-1]
            dest = f"{base_dest}/{file_name}"
            self.add_task(
                f"Download {file_name}",
                "ansible.builtin.get_url",
                url=url,
                dest=dest,
                owner=owner if owner else None,
                group=group if group else None,
                register=register,
                when=when,
            )
        return self

    def git_clone(
        self,
        task_name: str,
        repo: str,
        dest: str,
        owner: Optional[str] = None,
        group: Optional[str] = None,
        register: Optional[str] = None,
        when: Optional[Condition] = None,
        **kwargs: Any,
    ) -> "Play":
        args = {"repo": repo, "dest": dest}
        if owner:
            args["owner"] = owner
        if group:
            args["group"] = group
        args.update(kwargs)

        return self.add_task(
            task_name, modules["git"], register=register, when=when, **args
        )

    def ensure_directory(
        self,
        path: str,
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> "Play":
        stat_var = f"{Path(path).name}_stat"

        self.stat(f"Check if {path} exists", path, stat_var)
        self.create_directory(
            f"Create {path}",
            path,
            owner=owner,
            group=group,
            mode=mode,
            when=f"{stat_var}.stat.exists == false",
        )
        return self

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.name:
            d["name"] = self.name
        if self.hosts:
            d["hosts"] = self.hosts
        if self.become:
            d["become"] = True
        d["tasks"] = [t.to_dict() for t in self.tasks]
        return d

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            [self.to_dict()], sort_keys=False, default_flow_style=False
        )
