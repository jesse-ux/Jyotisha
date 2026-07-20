# Jyotisha Staging Infrastructure Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare `118.26.111.127` as a secure, isolated staging target with DNS, a separate Supabase project, and a protected GitHub staging environment.

**Architecture:** The Hong Kong VPS exposes only SSH, HTTP, and HTTPS. Application containers run behind Caddy, while staging data and authentication live in a separate Supabase project. GitHub Actions deploys through a dedicated Ed25519 key and pinned SSH host key.

**Tech Stack:** Ubuntu 24.04 LTS, OpenSSH, UFW, Docker Engine, Docker Compose, Caddy, Supabase, GitHub Actions Environments.

## Global Constraints

- Production server, production DNS, production Supabase, and production GitHub secrets are out of scope.
- Staging domain is exactly `staging.jyotisha.chat`.
- Staging host is exactly `118.26.111.127`.
- Application path is exactly `/opt/jyotisha-staging`.
- Runtime environment file is exactly `/opt/jyotisha-staging/.env.staging` with mode `0600`.
- SSH, Supabase, database, and model-provider credentials must be staging-specific.
- Do not expose container ports `3000` or `5200` on the host.
- Do not disable password SSH until both `ubuntu` admin-key login and `deploy` deploy-key login succeed in separate terminals.
- Do not execute a database reset against any linked remote project.

---

## File and Control-Plane Map

- Cloud provider console: OS image, rescue console, security group.
- Local Mac: deploy pair `~/.ssh/jyotisha-staging*` and admin pair `~/.ssh/jyotisha-staging-admin*`.
- VPS: `/home/deploy/.ssh/authorized_keys`, `/etc/ssh/sshd_config.d/00-jyotisha-staging.conf`, `/etc/docker/daemon.json`, `/opt/jyotisha-staging/.env.staging`.
- DNS provider: `A staging.jyotisha.chat -> 118.26.111.127`.
- Supabase Dashboard: a new staging project, Auth URL configuration, staging credentials.
- GitHub repository settings: Environment named `staging`, one secret, six variables.

### Task 1: Verify the Purchased VPS Before Configuration

**Interfaces:**
- Consumes: Provider account containing `118.26.111.127`.
- Produces: A reachable Ubuntu 24.04 x86_64 server with console recovery available.

- [ ] **Step 1: Verify provider-console facts**

In the provider console, confirm all of these values before continuing:

```text
Public IPv4: 118.26.111.127
Region: Hong Kong
Architecture: x86_64 / amd64
Operating system: Ubuntu 24.04 LTS
RAM: 4 GB
CPU: 2 vCPU
System disk: at least 40 GB
Console or rescue login: enabled
Automatic snapshot/backup: enabled if included
```

Expected: every value matches. If the architecture is ARM, the disk is below 40 GB, or no console/reinstall path exists, stop before configuring the server.

- [ ] **Step 2: Restrict the provider security group**

Create inbound rules:

```text
TCP 22   source 0.0.0.0/0     SSH during bootstrap
TCP 80   source 0.0.0.0/0     HTTP and ACME redirect
TCP 443  source 0.0.0.0/0     HTTPS
UDP 443  source 0.0.0.0/0     HTTP/3, optional but used by Caddy
```

Delete inbound rules for `3000`, `5200`, database ports, provider control panels, and unrestricted custom port ranges.

Expected: a provider-console screenshot or rule list contains only the four intended inbound rules.

- [ ] **Step 3: Test the initial provider login**

From the local Mac:

```bash
ssh ubuntu@118.26.111.127
```

Expected: a first-use host-key prompt followed by the provider's `ubuntu` password prompt, then an Ubuntu shell. Do not send the password in chat, GitHub, or shell history.

- [ ] **Step 4: Confirm machine identity from the server**

Run on the VPS:

```bash
uname -m
source /etc/os-release
printf '%s %s\n' "$ID" "$VERSION_ID"
free -h
df -h /
ip -brief address
```

Expected:

```text
x86_64
ubuntu 24.04
approximately 4 GiB RAM
at least 40 GB root disk
118.26.111.127 present on the public interface or provider NAT mapping
```

### Task 2: Create and Verify the Dedicated Deploy Identity

**Interfaces:**
- Consumes: Initial `ubuntu` access from Task 1.
- Produces: `ubuntu@118.26.111.127` authenticated by the admin key and `deploy@118.26.111.127` authenticated by the deploy key.

- [ ] **Step 1: Generate separate admin and deploy keys on the local Mac**

Run locally, not on the VPS:

```bash
test ! -e "$HOME/.ssh/jyotisha-staging-admin"
test ! -e "$HOME/.ssh/jyotisha-staging"
ssh-keygen -t ed25519 -a 64 -N '' -f "$HOME/.ssh/jyotisha-staging-admin" -C "jyotisha-staging-admin"
ssh-keygen -t ed25519 -a 64 -N '' -f "$HOME/.ssh/jyotisha-staging" -C "github-actions-jyotisha-staging"
chmod 600 "$HOME/.ssh/jyotisha-staging-admin"
chmod 600 "$HOME/.ssh/jyotisha-staging"
chmod 644 "$HOME/.ssh/jyotisha-staging-admin.pub"
chmod 644 "$HOME/.ssh/jyotisha-staging.pub"
ssh-keygen -lf "$HOME/.ssh/jyotisha-staging-admin.pub"
ssh-keygen -lf "$HOME/.ssh/jyotisha-staging.pub"
```

Expected: four key files are created and both fingerprints use `ED25519`. The admin private key remains only on the Mac. The deploy private key is later stored only in the GitHub `staging` Environment and must never be used for production.

- [ ] **Step 2: Install only the admin public key on the ubuntu account**

Run locally and type the server password only at the terminal prompt:

```bash
ssh-copy-id -i "$HOME/.ssh/jyotisha-staging-admin.pub" ubuntu@118.26.111.127
ssh -i "$HOME/.ssh/jyotisha-staging-admin" -o IdentitiesOnly=yes ubuntu@118.26.111.127 'id && sudo -n true'
```

Expected: the first command installs the public key; the second logs in as `ubuntu`. `sudo -n true` must exit `0`; if the provider requires a sudo password, keep the interactive admin session open and use `sudo` with the password typed directly at its prompt.

- [ ] **Step 3: Create the deploy user on the VPS**

Log in with the admin key and run:

```bash
ssh -i "$HOME/.ssh/jyotisha-staging-admin" -o IdentitiesOnly=yes ubuntu@118.26.111.127
sudo adduser --disabled-password --gecos "" deploy
sudo install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
sudo install -d -m 755 -o deploy -g deploy /opt/jyotisha-staging
```

Expected:

```bash
id deploy
sudo stat -c '%U %G %a %n' /home/deploy/.ssh /opt/jyotisha-staging
```

The output shows user `deploy`, `.ssh` mode `700`, and `/opt/jyotisha-staging` owned by `deploy`.

- [ ] **Step 4: Copy only the deploy public key to the VPS**

From a second local terminal:

```bash
scp -i "$HOME/.ssh/jyotisha-staging-admin" -o IdentitiesOnly=yes \
  "$HOME/.ssh/jyotisha-staging.pub" ubuntu@118.26.111.127:/tmp/jyotisha-staging.pub
```

Then in the authenticated `ubuntu` session:

```bash
sudo install -m 600 -o deploy -g deploy /tmp/jyotisha-staging.pub /home/deploy/.ssh/authorized_keys
sudo shred -u /tmp/jyotisha-staging.pub
```

Expected:

```bash
sudo stat -c '%U %G %a %n' /home/deploy/.ssh/authorized_keys
```

Output: `deploy deploy 600 /home/deploy/.ssh/authorized_keys`.

- [ ] **Step 5: Verify deploy-key login in a new terminal**

Keep the `ubuntu` admin session open. From the local Mac:

```bash
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127 'id && hostname'
```

Expected: exit code `0`; output contains `uid=` for `deploy`. Do not continue if this fails.

- [ ] **Step 6: Pin and compare the server host key**

On the VPS `ubuntu` session:

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

On the local Mac:

```bash
ssh-keyscan -t ed25519 -p 22 118.26.111.127 2>/dev/null > /tmp/jyotisha-staging-known-hosts
ssh-keygen -lf /tmp/jyotisha-staging-known-hosts
```

Expected: both fingerprints are identical. Preserve the exact line in `/tmp/jyotisha-staging-known-hosts` for GitHub Task 6. If they differ, stop and use the provider console to investigate.

### Task 3: Patch, Harden, and Add Swap

**Interfaces:**
- Consumes: Verified deploy-key login.
- Produces: Patched Ubuntu, 4 GB swap, key-only SSH, and host firewall rules.

- [ ] **Step 1: Install base administration packages**

Run from the authenticated `ubuntu` session with `sudo`:

```bash
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get dist-upgrade -y
sudo apt-get install -y ca-certificates curl git rsync ufw unattended-upgrades
sudo hostnamectl set-hostname jyotisha-staging
sudo timedatectl set-timezone UTC
sudo systemctl enable --now unattended-upgrades
```

Expected: all commands exit `0` and `hostnamectl --static` prints `jyotisha-staging`.

- [ ] **Step 2: Create swap only if the VPS has none**

Run with `sudo`:

```bash
if [ "$(swapon --noheadings | wc -l)" -eq 0 ]; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  printf '%s\n' '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi
sudo sysctl vm.swappiness=10
printf '%s\n' 'vm.swappiness=10' | sudo tee /etc/sysctl.d/60-jyotisha-staging.conf >/dev/null
```

Expected:

```bash
swapon --show
free -h
grep -F '/swapfile none swap sw 0 0' /etc/fstab
```

Output shows one 4 GB swap file and one matching `fstab` entry.

- [ ] **Step 3: Configure UFW before enabling it**

Run with `sudo`:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw allow 443/udp comment 'HTTP3'
sudo ufw --force enable
sudo systemctl enable --now ufw
sudo ufw status verbose
systemctl is-enabled ufw
```

Expected: UFW is active and enabled at boot; only `22/tcp`, `80/tcp`, `443/tcp`, and `443/udp` are allowed. Docker-published ports must still be reviewed separately because Docker can bypass UFW; the application Compose file may publish only 80/443.

- [ ] **Step 4: Harden SSH with a configuration snippet**

Run with `sudo`:

```bash
sudo install -m 600 /dev/null /etc/ssh/sshd_config.d/00-jyotisha-staging.conf
printf '%s\n' \
  'PubkeyAuthentication yes' \
  'PasswordAuthentication no' \
  'KbdInteractiveAuthentication no' \
  'PermitRootLogin no' \
  'X11Forwarding no' \
  'MaxAuthTries 3' \
  | sudo tee /etc/ssh/sshd_config.d/00-jyotisha-staging.conf >/dev/null
sudo sshd -t
sudo systemctl reload ssh
sudo sshd -T | grep -E '^(passwordauthentication|kbdinteractiveauthentication|permitrootlogin|pubkeyauthentication|maxauthtries) '
```

Expected: `sshd -t` emits nothing and exits `0`; the effective configuration shows password and keyboard-interactive authentication disabled, root login disabled, public-key authentication enabled, and `maxauthtries 3`. The `00-` prefix intentionally loads before provider-generated snippets such as `50-cloud-init.conf`, because OpenSSH uses the first obtained value for these settings.

- [ ] **Step 5: Re-test access before closing the original password session**

From the local Mac:

```bash
ssh -i "$HOME/.ssh/jyotisha-staging-admin" -o IdentitiesOnly=yes ubuntu@118.26.111.127 'printf "admin-key-ok\n"'
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127 'printf "deploy-key-ok\n"'
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o NumberOfPasswordPrompts=0 ubuntu@118.26.111.127 true
```

Expected: the first two commands print `admin-key-ok` and `deploy-key-ok`. The password-only command is rejected. Only now close the original password-authenticated session.

### Task 4: Install Docker and Bound Its Disk Usage

**Interfaces:**
- Consumes: Hardened server from Task 3.
- Produces: Docker Engine and Compose available to `deploy` with bounded local logs.

- [ ] **Step 1: Install Docker from Docker's official apt repository**

Use the authenticated `ubuntu` admin-key session and enter `sudo -i`. The `deploy` user intentionally has no general sudo access. Run:

```bash
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
printf '%s\n' \
  'Types: deb' \
  'URIs: https://download.docker.com/linux/ubuntu' \
  "Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")" \
  'Components: stable' \
  "Architectures: $(dpkg --print-architecture)" \
  'Signed-By: /etc/apt/keyrings/docker.asc' \
  > /etc/apt/sources.list.d/docker.sources
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
```

Expected: packages come from `download.docker.com`; no convenience `curl | sh` installer is used. Reference: <https://docs.docker.com/engine/install/ubuntu/>.

- [ ] **Step 2: Configure bounded Docker logs**

Run in the `sudo -i` admin shell on the fresh server:

```bash
printf '%s\n' \
  '{' \
  '  "log-driver": "local",' \
  '  "log-opts": {' \
  '    "max-size": "10m",' \
  '    "max-file": "5"' \
  '  }' \
  '}' \
  > /etc/docker/daemon.json
systemctl restart docker
```

Expected: `docker info --format '{{.LoggingDriver}}'` prints `local`.

- [ ] **Step 3: Allow the deploy user to run Docker**

Run in the `sudo -i` admin shell:

```bash
usermod -aG docker deploy
chown -R deploy:deploy /opt/jyotisha-staging
```

Log out and reconnect as deploy, then run:

```bash
docker version
docker compose version
docker run --rm hello-world
```

Expected: all three commands succeed without `sudo`.

- [ ] **Step 4: Record the clean-server capacity baseline**

Run as deploy:

```bash
free -h
df -h /
docker system df
systemctl is-active docker
```

Expected: approximately 4 GB RAM plus 4 GB swap, at least 20 GB free disk, and Docker `active`.

### Task 5: Create DNS and the Isolated Supabase Staging Project

**Interfaces:**
- Consumes: Working HTTPS ports and access to DNS/Supabase dashboards.
- Produces: `staging.jyotisha.chat` resolving to the VPS and an empty staging Supabase project at the current schema.

- [ ] **Step 1: Create the staging DNS record**

In the authoritative DNS provider for `jyotisha.chat`, create exactly:

```text
Type: A
Name/Host: staging
Value: 118.26.111.127
TTL: 600 seconds (or provider default if fixed)
Proxy/CDN: DNS only during bootstrap
```

Verify locally:

```bash
dig +short A staging.jyotisha.chat
```

Expected: `118.26.111.127` and no production IP.

- [ ] **Step 2: Create a separate Supabase project**

In the Supabase organization, create a new project with:

```text
Project name: jyotisha-staging
Region: Singapore / ap-southeast-1
Database password: newly generated and stored in password manager
Production restore/data import: disabled
```

Expected: the project Dashboard URL has a new project reference different from `vtvnfqmonbfuxmqkqdlc`.

- [ ] **Step 3: Configure staging Auth URLs**

In `Authentication -> URL Configuration`, set:

```text
Site URL: https://staging.jyotisha.chat
Redirect URL: https://staging.jyotisha.chat/**
```

Do not add the production URL to the staging project.

- [ ] **Step 4: Link the local CLI to staging and preview migrations**

From the repository on the local Mac:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npx supabase login
read -r -p 'Paste the jyotisha-staging project reference: ' STAGING_PROJECT_REF
test "$STAGING_PROJECT_REF" != 'vtvnfqmonbfuxmqkqdlc'
npx supabase link --project-ref "$STAGING_PROJECT_REF"
npx supabase db push --dry-run
```

Expected: the production-project guard passes, and the dry run lists the repository migrations without applying them. Supabase documents `--dry-run` for exactly this preview: <https://supabase.com/docs/reference/cli/installing-the-cli#supabase-db-push>.

- [ ] **Step 5: Apply migrations only after reviewing the dry run**

Run:

```bash
npx supabase db push
npx supabase migration list
```

Expected: `db push` succeeds and local/remote migration versions align. If any migration fails, stop; do not mark migration history manually and do not fall back to production credentials.

- [ ] **Step 6: Create the server-only staging environment file**

Collect from the staging project Dashboard: project URL, publishable/anon key, service-role key, and Session Pooler database URL. Create low-limit staging model-provider keys. Then log in as deploy and run the following interactive sequence. Secret prompts do not echo their values:

```bash
cd /opt/jyotisha-staging
read -r -p 'Staging Supabase URL: ' STAGING_SUPABASE_URL
read -r -s -p 'Staging Supabase publishable/anon key: ' STAGING_SUPABASE_ANON_KEY; printf '\n'
read -r -s -p 'Staging Supabase service-role key: ' STAGING_SUPABASE_SERVICE_KEY; printf '\n'
read -r -s -p 'Staging Session Pooler database URL: ' STAGING_DB_URL; printf '\n'
read -r -p 'Staging admin email: ' STAGING_ADMIN_EMAIL
read -r -p 'Staging default model id: ' STAGING_DEFAULT_MODEL
read -r -s -p 'Staging LLM_MODELS_JSON: ' STAGING_MODEL_CATALOG; printf '\n'
read -r -s -p 'Staging OpenAI key (press Enter if unused): ' STAGING_OPENAI_KEY; printf '\n'
read -r -s -p 'Staging DeepSeek key (press Enter if unused): ' STAGING_DEEPSEEK_KEY; printf '\n'
read -r -s -p 'Staging VedAstro key: ' STAGING_VEDASTRO_KEY; printf '\n'
umask 077
printf '%s\n' \
  'APP_ENV_FILE=../.env.staging' \
  'CADDYFILE_PATH=./Caddyfile.staging' \
  'SITE_ADDRESS=https://staging.jyotisha.chat' \
  'JYOTISH_API_BASE=http://api:5200' \
  "NEXT_PUBLIC_SUPABASE_URL=$STAGING_SUPABASE_URL" \
  "NEXT_PUBLIC_SUPABASE_ANON_KEY=$STAGING_SUPABASE_ANON_KEY" \
  "SUPABASE_SERVICE_ROLE_KEY=$STAGING_SUPABASE_SERVICE_KEY" \
  "SUPABASE_DB_URL=$STAGING_DB_URL" \
  "ADMIN_EMAILS=$STAGING_ADMIN_EMAIL" \
  "LLM_DEFAULT_MODEL_ID=$STAGING_DEFAULT_MODEL" \
  "LLM_MODELS_JSON=$STAGING_MODEL_CATALOG" \
  "OPENAI_API_KEY=$STAGING_OPENAI_KEY" \
  "DEEPSEEK_API_KEY=$STAGING_DEEPSEEK_KEY" \
  'VEDASTRO_GATEWAY_MODE=official_first' \
  'VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api' \
  'VEDASTRO_ENABLE_NETWORK=1' \
  'VEDASTRO_TIMEOUT_SECONDS=20' \
  "VEDASTRO_API_KEY=$STAGING_VEDASTRO_KEY" \
  > .env.staging
chmod 600 .env.staging
unset STAGING_SUPABASE_URL STAGING_SUPABASE_ANON_KEY STAGING_SUPABASE_SERVICE_KEY STAGING_DB_URL
unset STAGING_ADMIN_EMAIL STAGING_DEFAULT_MODEL STAGING_MODEL_CATALOG STAGING_OPENAI_KEY STAGING_DEEPSEEK_KEY STAGING_VEDASTRO_KEY
```

Do not use production values in any prompt. If a model provider is unused, its key may be blank only when `LLM_MODELS_JSON` does not reference that environment variable.

Verify names without printing values:

```bash
awk -F= 'NF && $1 !~ /^#/ {print $1}' .env.staging | sort
stat -c '%U %G %a %n' .env.staging
```

Expected: all required names appear and mode is `600` owned by deploy.

### Task 6: Create the Protected GitHub Staging Environment

**Interfaces:**
- Consumes: Deploy private key, verified known-hosts line, VPS and DNS values.
- Produces: GitHub Environment `staging` with one secret and six variables.

- [ ] **Step 1: Create the Environment in GitHub UI**

Open:

```text
Repository -> Settings -> Environments -> New environment
Name: staging
```

Set deployment branches to `Selected branches and tags`, then allow only branch pattern `staging`.

Expected: the Environment page displays `staging` and its branch policy.

- [ ] **Step 2: Add the staging SSH private key as an Environment secret**

Create exactly one Environment secret:

```text
Name: STAGING_SSH_PRIVATE_KEY
Value: complete contents of ~/.ssh/jyotisha-staging
```

Do not put this key in repository-level secrets and do not reuse `PRODUCTION_SSH_PRIVATE_KEY`.

- [ ] **Step 3: Add non-secret Environment variables**

Create the first five variables with the literal values shown:

```text
STAGING_HOST=118.26.111.127
STAGING_PORT=22
STAGING_USER=deploy
STAGING_PATH=/opt/jyotisha-staging
STAGING_URL=https://staging.jyotisha.chat
```

Create the sixth variable with name `STAGING_KNOWN_HOSTS`. Its value is the complete output of this local command:

```bash
cat /tmp/jyotisha-staging-known-hosts
```

Paste the full line beginning with `118.26.111.127` or `[118.26.111.127]:22`; do not paste only the fingerprint.

- [ ] **Step 4: Verify the Environment has no production credentials**

Expected Environment inventory:

```text
Secrets (1): STAGING_SSH_PRIVATE_KEY
Variables (6): STAGING_HOST, STAGING_PORT, STAGING_USER, STAGING_PATH, STAGING_URL, STAGING_KNOWN_HOSTS
Allowed branch: staging
```

GitHub Environment secrets become available only to jobs that explicitly reference that Environment: <https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments>.

### Task 7: Infrastructure Readiness Gate

**Interfaces:**
- Consumes: Tasks 1–6.
- Produces: A go/no-go result for repository deployment automation.

- [ ] **Step 1: Run the local SSH and DNS checks**

```bash
dig +short A staging.jyotisha.chat
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127 \
  'hostname; free -h; df -h /; docker version --format "{{.Server.Version}}"; docker compose version; stat -c "%a %n" /opt/jyotisha-staging/.env.staging'
```

Expected: correct IP, hostname `jyotisha-staging`, Docker/Compose versions, and `.env.staging` mode `600`.

- [ ] **Step 2: Confirm no unintended public ports**

Run locally:

```bash
nc -vz 118.26.111.127 22
nc -vz 118.26.111.127 80
nc -vz 118.26.111.127 443
nc -vz -w 3 118.26.111.127 3000
nc -vz -w 3 118.26.111.127 5200
```

Expected: 22 is reachable. Before application deployment, 80/443 may refuse because nothing is listening; this is acceptable. Ports 3000 and 5200 must not connect.

- [ ] **Step 3: Reboot once and verify the bootstrap survives**

From the authenticated `ubuntu` admin-key session:

```bash
sudo systemctl reboot
```

Wait for the provider console to report the VPS online, then run locally:

```bash
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127 \
  'hostname; swapon --show; systemctl is-active docker; systemctl is-active ufw'
```

Expected: deploy-key login works after reboot, swap is present, Docker is `active`, and UFW is active.

- [ ] **Step 4: Record the go/no-go decision**

Go only if all are true:

```text
ubuntu admin key works
deploy key works
root/password SSH is disabled
host-key fingerprints match
Docker and Compose work as deploy
4 GB swap exists
DNS resolves only to 118.26.111.127
staging Supabase project reference differs from production
migrations applied successfully to staging
.env.staging exists with mode 0600
GitHub staging Environment contains only staging credentials
```

If any item is false, stop before implementing or running the deployment workflow.
