#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml

from pathlib import Path
from utils.ansible import Play

if __name__ == "__main__":
    tools_dir = "/home/mocha/tools"
    tools_ad_dir = f"{tools_dir}/ad"
    tools_pivot_dir = f"{tools_dir}/pivot"
    tools_transfer_dir = f"{tools_dir}/transfer"
    tools_transfer_tooling_dir = f"{tools_transfer_dir}/tooling"
    tools_transfer_tooling_pivot_dir = f"{tools_transfer_tooling_dir}/pivot"
    tool_categories = [
        "ad",
        "av_evasion",
        "c2_frameworks",
        "password_mutation",
        "pivot",
        "sniffing",
        "transfer",
        "web-application",
    ]

    plays: list[Play] = []

    install_deps = (
        Play(name="Install (some) Dependencies", hosts="localhost", become=True)
        .add_apt("install pipx", "pipx", update_cache="yes")
        .add_apt("remove python3-impacket", "python3-impacket", state="absent")
        .add_apt("remove impacket-scripts", "impacket-scripts", state="absent")
        .add_apt("install ntpdate", "ntpsec-ntpdate", update_cache="yes")
        .add_apt("install sshpass", "sshpass", update_cache="yes")
        .add_apt("install gh", "gh", update_cache="yes")
    )

    tools_git = [
        "https://github.com/ly4k/Certipy.git",
        "https://github.com/Pennyw0rth/NetExec.git",
        "https://github.com/dirkjanm/BloodHound.py.git",
        "https://github.com/CravateRouge/bloodyAD.git",
        "https://github.com/gatariee/adidnsdump.git",
        "https://github.com/gentilkiwi/mimikatz.git",
        "https://github.com/NH-RED-TEAM/RustHound.git",
        "https://github.com/g0h4n/RustHound-CE.git",
        "https://github.com/aniqfakhrul/powerview.py.git",
        "https://github.com/lgandx/Responder.git",
        "https://github.com/p0dalirius/coercer.git",
        "https://github.com/zblurx/dploot.git",
        "https://github.com/login-securite/DonPAPI.git",
        "https://github.com/micahvandeusen/gMSADumper.git",
        "https://github.com/franc-pentest/ldeep.git",
        "https://github.com/trustedsec/Titanis.git",
        "https://github.com/Macmod/ldapx.git",
        "https://github.com/gatariee/minrm.git",
        "https://github.com/ShutdownRepo/pywhisker.git",
        "https://github.com/dirkjanm/PKINITtools.git",
        "https://github.com/Greenwolf/ntlm_theft.git",
        "https://github.com/dirkjanm/krbrelayx.git",
        
    ]
    tools_transfer_git = [
        "https://github.com/Flangvik/SharpCollection.git",
    ]

    # be careful with these!!
    tools_standalone = [
        "https://github.com/SpecterOps/SharpHound/releases/download/v2.12.0/SharpHound_v2.12.0_windows_x86.zip",
        "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/refs/heads/master/Recon/PowerView.ps1",
        "https://github.com/DominicBreuker/pspy/releases/download/v1.2.1/pspy64",
        "https://github.com/vinsworldcom/NetCat64/releases/download/1.11.6.4/nc64.exe",
        "https://github.com/peass-ng/PEASS-ng/releases/download/20260501-5805575d/linpeas.sh",
        "https://github.com/peass-ng/PEASS-ng/releases/download/20260501-5805575d/winPEASx64.exe",
        "https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_agent_0.8.3_windows_amd64.zip",
        "https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz",
    ]

    fetch_tools = (
        Play(name="Install Tools", hosts="localhost", become=False)
        .ensure_directory(tools_dir, owner="mocha", group="mocha")
    )
    for category in tool_categories:
        fetch_tools.ensure_directory(f"{tools_dir}/{category}", owner="mocha", group="mocha")
    fetch_tools.ensure_directory(tools_transfer_tooling_dir, owner="mocha", group="mocha")
    fetch_tools.ensure_directory(tools_transfer_tooling_pivot_dir, owner="mocha", group="mocha")
    fetch_tools.mass_clone(
        tools_ad_dir,
        tools_git,
        owner="mocha",
        group="mocha",
    ).mass_clone(
        tools_transfer_tooling_dir,
        tools_transfer_git,
        owner="mocha",
        group="mocha",
    ).mass_wget(
        tools_transfer_tooling_dir,
        tools_standalone,
        owner="mocha",
        group="mocha",
    )

    '''
    Handling ligolo case:
    - Agent needs to be placed in the pivot directory under the transfer/tooling/pivot directory
    - Proxy needs to be placed in the pivot directory defined in the tools_pivot_dir variable
    '''

    # ligolo agent needs to be placed in the pivot directory
    fetch_tools.sh(
        task_name="Place ligolo agent in pivot directory",
        cmd=f"cp {tools_transfer_tooling_dir}/ligolo-ng_agent_0.8.3_windows_amd64.zip {tools_transfer_tooling_pivot_dir}/ligolo-ng_agent_0.8.3_windows_amd64.zip",
    )

    # Proxy needs to be placed in the pivot directory defined in the tools_pivot_dir variable
    fetch_tools.sh(
        task_name="Place proxy in pivot directory",
        cmd=f"cp {tools_transfer_tooling_dir}/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz {tools_pivot_dir}/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz",
    )

    # Unzip the proxy in the pivot directory defined in the tools_pivot_dir variable
    fetch_tools.sh(
        task_name="Unzip proxy in pivot directory",
        cmd=f"tar -xzf {tools_pivot_dir}/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz -C {tools_pivot_dir}",
    )

    # Make the proxy executable
    fetch_tools.sh(
        task_name="Make proxy executable",
        cmd=f"chmod +x {tools_pivot_dir}/proxy",
    )

    # Unzip the agent in the pivot directory defined in the tools_transfer_tooling_pivot_dir variable
    fetch_tools.sh(
        task_name="Unzip agent in pivot directory",
        cmd=f"unzip {tools_transfer_tooling_pivot_dir}/ligolo-ng_agent_0.8.3_windows_amd64.zip -d {tools_transfer_tooling_pivot_dir}",
    )


    install_tools = (
        Play(name="Setup Tools via pipx", hosts="localhost", become=False) # run as normal user
        .ensure_directory(tools_dir, owner="mocha", group="mocha")
        .ensure_directory(tools_ad_dir, owner="mocha", group="mocha")
        .ensure_directory(tools_transfer_tooling_dir, owner="mocha", group="mocha")
        .ensure_directory(tools_transfer_tooling_pivot_dir, owner="mocha", group="mocha")
        .sh(
            task_name="pipx install tools",
            cmd=f"""
for category in {tools_dir}/*/; do
    for d in "$category"*/; do
        if [ -f "$d/setup.py" ] || [ -f "$d/pyproject.toml" ]; then
            echo "Installing $d with pipx"
            pipx install "$d"
        fi
    done
done
"""
        )
        .sh(
            task_name="pipx install impacket",
            cmd="pipx install impacket",
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
            "https://vscode.download.prss.microsoft.com/dbazure/download/stable/6f17636121051a53c88d3e605c491d22af2ba755/code_1.109.5-1771531656_amd64.deb",
            dest="/tmp/code.deb",
            register="vscode_deb",
            when="vscode_stat.stat.exists == False and vscode_deb_stat.stat.exists == False",
        )
        .sh(
            "Install VSCode",
            "dpkg -i /tmp/code.deb",
        )
    )

    # refer to this if you hate the rust syntax
    install_tailscale = Play(name="Install Tailscale", hosts="localhost", become=True)

    install_tailscale.stat(
        "Check if Tailscale is installed", "/usr/bin/tailscale", "tailscale_stat"
    )

    install_tailscale.sh(
        task_name="Add GPG Keys",
        cmd="""
curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
        """,
        when="tailscale_stat.stat.exists == false",
    )

    install_tailscale.add_apt(
        task_name="Install Tailscale",
        pkg="tailscale",
        update_cache="yes",
        when="tailscale_stat.stat.exists == false",
    )

    install_tailscale.systemd_service(
        task_name="Enable and Start Tailscale",
        name="tailscaled",
        state="started",
        enabled=True,
    )

    install_wireguard = (
        Play(name="Install Wireguard", hosts="localhost", become=True)
        .add_apt("install wireguard", "wireguard", update_cache="yes")
        .add_apt("install wg-tools", "wireguard-tools", update_cache="yes")
    )

    install_fonts = (
        Play(name="Install Fonts", hosts="localhost", become=True)
        .wget("fetch jb-mono", "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/JetBrainsMono.zip", dest="/tmp/JetBrainsMono.zip")
        .sh("unzip jb-mono", "unzip /tmp/JetBrainsMono.zip -d /usr/share/fonts/truetype/jb-mono")
        .sh("fc-cache", "fc-cache -fv")
    )

    wallpaper_user = "mocha"
    wallpaper_dest = f"/home/{wallpaper_user}/Pictures/wallpaper.jpg"
    install_wallpaper = (
        Play(name="Set desktop wallpaper", hosts="localhost", become=True)
        .create_directory(
            f"Ensure {wallpaper_user} Pictures directory",
            f"/home/{wallpaper_user}/Pictures",
            owner=wallpaper_user,
            group=wallpaper_user,
            mode="0755",
        )
        .copy(
            "Install wallpaper image from repo assets",
            src="{{ playbook_dir }}/assets/23.jpg",
            dest=wallpaper_dest,
            owner=wallpaper_user,
            group=wallpaper_user,
            mode="0644",
        )
        .sh(
            "Apply wallpaper (GNOME / KDE Plasma / XFCE)",
            f"""\
uid=$(id -u {wallpaper_user})
WP_FILE="{wallpaper_dest}"
WP_URI="file://{wallpaper_dest}"
run_as() {{ sudo -u {wallpaper_user} env "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus" "$@"; }}

# GNOME
if command -v gsettings >/dev/null 2>&1; then
  run_as gsettings set org.gnome.desktop.background picture-uri "$WP_URI" || true
  run_as gsettings set org.gnome.desktop.background picture-uri-dark "$WP_URI" || true
fi

# KDE Plasma 
if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
  run_as plasma-apply-wallpaperimage "$WP_FILE" || true
fi

# XFCE
if command -v xfconf-query >/dev/null 2>&1; then
  run_as bash -c 'WP_FILE="$1"; for prop in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep last-image || true); do
    if xfconf-query -c xfce4-desktop -p "$prop" >/dev/null 2>&1; then
      xfconf-query -c xfce4-desktop -p "$prop" -s "$WP_FILE" || true
    else
      xfconf-query -c xfce4-desktop -p "$prop" -n -t string -s "$WP_FILE" || true
    fi
  done' bash "$WP_FILE"
fi
""",
        )
    )

    misc_stuff_lmao = (
        Play(name="Misc Stuff", hosts="localhost", become=True)
        .stat("Check if rockyou is gz'ed", "/usr/share/wordlists/rockyou.txt.gz", "rockyou_stat")
        .sh("gunzip rockyou", "gunzip /usr/share/wordlists/rockyou.txt.gz", when="rockyou_stat.stat.exists == true")
    )

    zsh_user = wallpaper_user
    install_zsh_omz = (
        Play(name="Install zsh and Oh My Zsh", hosts="localhost", become=True)
        .add_apt("install zsh", "zsh", update_cache="yes")
        .add_apt("install curl for Oh My Zsh installer", "curl", update_cache="yes")
        .add_apt("install git for Oh My Zsh", "git", update_cache="yes")
        .stat("Check Oh My Zsh", f"/home/{zsh_user}/.oh-my-zsh/oh-my-zsh.sh", "ohmyzsh_stat")
        .sh(
            "Install Oh My Zsh unattended",
            f"""sudo -u {zsh_user} env RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended""",
            when="ohmyzsh_stat.stat.exists == false",
        )
        .add_task(
            f"Set default shell to zsh for {zsh_user}",
            "ansible.builtin.user",
            name=zsh_user,
            shell="/usr/bin/zsh",
        )
    )

    # QTerminal (LXQt) — keys from lxqt/qterminal properties.cpp / qtermwidget enums
    configure_qterminal = (
        Play(name="Configure QTerminal appearance", hosts="localhost", become=True)
        .add_apt("install qterminal", "qterminal", update_cache="yes")
        .create_directory(
            "Ensure qterminal config directory exists",
            f"/home/{wallpaper_user}/.config/qterminal.org",
            owner=wallpaper_user,
            group=wallpaper_user,
            mode="0755",
        )
        .sh(
            "Merge QTerminal settings into qterminal.ini",
            f"""sudo -u {wallpaper_user} python3 <<'PY'
import configparser
import pathlib

path = pathlib.Path.home() / ".config" / "qterminal.org" / "qterminal.ini"
path.parent.mkdir(parents=True, exist_ok=True)
cfg = configparser.ConfigParser()
cfg.optionxform = str
if path.is_file():
    cfg.read(path)
if not cfg.has_section("General"):
    cfg.add_section("General")
G = cfg["General"]
updates = {{
    "fontFamily": "JetBrainsMono Nerd Font",
    "fontSize": "14",
    "colorScheme": "Kali-Dark",
    "TerminalTransparency": "2",
    "TerminalMargin": "5",
    "TerminalBackgroundMode": "0",
    "TerminalBackgroundImage": "",
    "ScrollbarPosition": "2",
    "TabsPosition": "0",
    "KeyboardCursorShape": "2",
    "KeyboardCursorBlink": "false",
    "BoldIntense": "true",
    "showTerminalSizeHint": "true",
    "enabledBidiSupport": "true",
    "UseFontBoxDrawingChars": "true",
    "Borderless": "false",
    "focusOnMoueOver": "false",
    "ChangeWindowTitle": "true",
    "ChangeWindowIcon": "true",
    "TerminalsPreset": "0",
}}
for k, v in updates.items():
    G[k] = str(v)
if cfg.has_option("General", "guiStyle"):
    cfg.remove_option("General", "guiStyle")
with path.open("w") as f:
    cfg.write(f)
PY
""",
        )
    )

    plays.append(install_deps)
    plays.append(fetch_tools)
    plays.append(install_tools)
    plays.append(install_zsh_omz)
    plays.append(install_vscode)
    plays.append(install_tailscale)
    plays.append(install_wireguard)
    plays.append(install_fonts)
    plays.append(install_wallpaper)
    plays.append(configure_qterminal)
    plays.append(misc_stuff_lmao)

    playbook = yaml.safe_dump(
        [play.to_dict() for play in plays],
        sort_keys=False,
        default_flow_style=False,
    )

    print(playbook)
    Path("playbook.yml").write_text(playbook)
