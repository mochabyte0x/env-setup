update packages before running ansible

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install ansible -y

sudo ansible-playbook playbook.yml
```