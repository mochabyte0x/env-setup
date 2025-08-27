#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml

from pathlib import Path
from utils.ansible import Play

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
            owner="kali",
            group="kali",
        )
        .mass_wget(
            tools_dir_standalone,
            tools_standalone,
            owner="kali",
            group="kali",
        )
    )

    install_vscode = (
        Play(name="Install VSCode", hosts="localhost", become=True)
        .stat("Check if VSCode is installed", "/usr/bin/code", "vscode_stat")
        .stat(
            "Check if VSCode deb is downloaded",
            "/tmp/code.deb",
            "vscode_deb_stat",
        )
        .wget(
            "Download VSCode Debian Package",
            # grab latest with:
            # curl 'https://update.code.visualstudio.com/latest/linux-deb-x64/stable'
            "https://vscode.download.prss.microsoft.com/dbazure/download/stable/6f17636121051a53c88d3e605c491d22af2ba755/code_1.103.2-1755709794_amd64.deb",
            dest="/tmp/code.deb",
            register="vscode_deb",
            when="vscode_stat.stat.exists == False and vscode_deb_stat.stat.exists == False",
        )
        .sh(
            "Install VSCode",
            "dpkg -i /tmp/code.deb",
        )
    )

    plays.append(install_packages)
    plays.append(fetch_tools)
    plays.append(install_vscode)

    playbook = yaml.safe_dump(
        [play.to_dict() for play in plays],
        sort_keys=False,
        default_flow_style=False,
    )

    print(playbook)
    Path("playbook.yml").write_text(playbook)
