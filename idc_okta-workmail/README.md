## OktaIdCWorkMailLambdaExample

Example script creates AWS Lambda which runs every 15 minutes and performs users synchronization between 
IdentityCenter and WorkMail.

### General Workflow

1. Edit `app.py` file providing your accountId and region. 
2. Also enter needed details for you Lambda environment in `app.py` file.
3. Prepare your local environment for local testing: 

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install .
```

4. Prepare your stack - change `cdk.json` file providing full path to your python within created virtual environment
5. Bootstrap package:

```bash
cdk bootstrap
```

6. Synthesize package

```bash
cdk synthesize
```

7. Deploy your package

```bash
cdk deploy
```
