## Run locally

```bash
x86brew tap azure/functions
x86brew install azure-functions-core-tools@4
```

```bash
ENV_NAME="x86python39"
CONDA_SUBDIR=osx-64 micromamba create -n $ENV_NAME python=3.9
micromamba activate $ENV_NAME
pip install -r requirements.txt
pip install "fastapi[all]"
```

```bash
/usr/local/bin/func start
```

or run fully local with:
```bash
uvicorn app:app --reload
```
