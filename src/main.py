#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pathlib import Path

import yaml

Condition = Union[str, List[str]]

modules = {
    "apt": "ansible.builtin.apt",
    "file": "ansible.builtin.file",
    "git": "ansible.builtin.git",
    "shell": "ansible.builtin.shell",
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
        owner: Optional[str] = None,
        group: Optional[str] = None,
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
                owner=owner,
                group=group,
                register=register,
                when=when,
            )
        return self

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
                owner=owner,
                group=group,
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


if __name__ == "__main__":
    tools_dir = "/home/kali/tools"
    tools_dir_standalone = "/home/kali/tools/standalone"

    plays: list[Play] = []

    install_packages = (
        Play(name="Install Packages", hosts="localhost", become=True)
        .add_apt("install pipx", "pipx", update_cache="yes")
        .add_apt("install ntpdate", "ntpsec-ntpdate", update_cache="yes")
    )

    tools_git = [
        "https://github.com/ly4k/Certipy.git",
        "https://github.com/fortra/impacket.git",
        "https://github.com/Pennyw0rth/NetExec.git",
        "https://github.com/dirkjanm/BloodHound.py.git",
        "https://github.com/CravateRouge/bloodyAD.git",
        "https://github.com/dirkjanm/adidnsdump.git",
        "https://github.com/gentilkiwi/mimikatz.git",
        "https://github.com/Flangvik/SharpCollection.git",
        "https://github.com/NH-RED-TEAM/RustHound.git",
        "https://github.com/g0h4n/RustHound-CE.git",
        "https://github.com/aniqfakhrul/powerview.py.git",
        "https://github.com/GhostPack/Rubeus.git",
        "https://github.com/GhostPack/Certify.git",
        "https://github.com/lgandx/Responder.git",
        "https://github.com/p0dalirius/coercer.git",
        "https://github.com/zblurx/dploot.git",
        "https://github.com/login-securite/DonPAPI.git",
    ]

    # be careful with these!!
    tools_standalone = [
        "https://github.com/SpecterOps/SharpHound/releases/download/v2.7.1/SharpHound_v2.7.1_windows_x86.zip",
        "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/refs/heads/master/Recon/PowerView.ps1",
    ]

    fetch_tools = (
        Play(name="Install Tools", hosts="localhost", become=False)
        .ensure_directory(tools_dir, owner="kali", group="kali")
        .ensure_directory(tools_dir_standalone, owner="kali", group="kali")
        .mass_clone(
            tools_dir,
            tools_git,
        )
        .mass_wget(
            tools_dir_standalone,
            tools_standalone,
        )
    )

    plays.append(install_packages)
    plays.append(fetch_tools)

    playbook = yaml.safe_dump(
        [play.to_dict() for play in plays],
        sort_keys=False,
        default_flow_style=False,
    )

    print(playbook)
    Path("playbook.yml").write_text(playbook)
