# Running on a Pixel Chromebook

This release analyzes a small public CSV snapshot on CPU. It does not require a
GPU or a local deep-learning environment.

## Set up the Linux terminal

If Linux is already enabled, open Terminal and continue below. Otherwise use
**Settings → About ChromeOS → Developers → Linux development environment** on a
supported device. Google's [official instructions](https://support.google.com/chromebook/answer/9145439?hl=en)
describe availability and setup. Device support and administrator settings vary.

In the Linux terminal:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
python3 --version
```

Use Python 3.10 or newer. If the installed Linux environment provides an older
version, use a supported newer Linux environment or a remote Python environment;
do not replace the system Python in place.

## Obtain the project

Clone the repository in your Linux terminal:

```bash
git clone https://github.com/ju2501/lnpdb-hhes-benchmark.git
cd lnpdb-hhes-benchmark
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If using a downloaded ZIP, extract it in Linux files,
open a terminal in the extracted project directory,
and start at `python3 -m venv .venv`.

The `.venv` keeps these analysis packages separate from a previous Chemprop or
conda installation. Do not upgrade an existing LiON environment to run this code.

## Run the reproducible analysis

```bash
lnpdb-hhes fetch
lnpdb-hhes benchmark
lnpdb-hhes candidates
lnpdb-hhes candidates --vary helper-cholesterol --out outputs/helper_cholesterol
python -m unittest discover -s tests -v
```

Results are in `outputs/`. Open the SVG files in Chrome or a vector editor; CSVs
can be viewed in a spreadsheet application. Edit copies, not the hashed input
files. To skip figure creation, use `lnpdb-hhes benchmark --no-figures`.

On a new terminal session:

```bash
cd lnpdb-hhes-benchmark
source .venv/bin/activate
```

## Git workflow

After editing code or documentation:

```bash
python -m unittest discover -s tests -v
git status --short
git add README.md docs src tests
git diff --cached --stat
git diff --cached
git commit -m "Describe the analysis change"
git push
```

GitHub authentication for push depends on your local setup. Follow GitHub's
[HTTPS authentication guidance](https://docs.github.com/en/get-started/git-basics/remote-repositories#cloning-with-https-urls).
Never put a token inside a repository file or command saved in documentation.

## If a command fails

| Message | Action |
|---|---|
| `lnpdb-hhes: command not found` | Activate `.venv`; try `python -m lnpdb_hhes --help`. |
| `externally-managed-environment` | Install inside `.venv`, not into system Python. |
| Missing snapshot CSV | Run `lnpdb-hhes fetch`. |
| Checksum mismatch | Preserve any manual edits elsewhere, then run `fetch --refresh`. |
| Network error on first download | Check access to `raw.githubusercontent.com`; an existing verified cache works offline. |
| No explicitly included groups | Complete source review in a copy of the curation template. |
| `unsupported:model_type=Jurkat` | Keep the true cell identity; the pinned model schema lacks that category. |

The pipeline was validated in a Linux Python runtime, not on the user's physical
Chromebook. RAM and runtime on that device should be measured on the first run.
