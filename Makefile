help:
	@echo "install - install a virtualenv for development"
	@echo "lint - check source code with flake8"
	@echo "test - run unit tests"
	@echo "coverage - check code coverage"
	@echo "build env={env} - package new code and update the function in the cloud"
	@echo "describe env={env} - describe cloud stack"
	@echo "check env={env} - check the state of one function"
	@echo "clean - remove build, test, coverage and Python artifacts locally"
	@echo "tear-down env={env} - completely destroy stack in the cloud -- be cautious"

.PHONY: venv
venv:
	@test -d "venv" || mkdir -p "venv"
	@rm -Rf "venv"
	@python3 -m venv "venv"
	@/bin/bash -c "source venv/bin/activate"

install: upgrade-pip install-deploy install-backend install-cdkproxy install-tests install-integration-tests install-custom-auth install-userguide

upgrade-pip:
	pip install --upgrade pip setuptools

install-deploy:
	pip install -r deploy/requirements.txt

install-backend:
	pip install -r backend/requirements.txt

install-cdkproxy:
	pip install -r backend/dataall/base/cdkproxy/requirements.txt

install-tests:
	pip install -r tests/requirements.txt

install-integration-tests:
	pip install -r tests_new/integration_tests/requirements.txt

install-custom-auth:
	pip install -r deploy/custom_resources/custom_authorizer/requirements.txt

install-userguide:
	pip install -r documentation/userguide/requirements.txt

lint:
	pip install ruff
	ruff check --fix
	ruff format

bandit:
	pip install bandit
	python -m bandit -r backend/ | tee bandit.log || true

check-security: upgrade-pip install-backend install-cdkproxy
	pip install bandit
	pip install safety
	bandit -lll -r backend
	safety check --ignore=51668,70612,70624

checkov-synth: upgrade-pip install-backend install-cdkproxy install-tests
	export PYTHONPATH=./backend:/./tests && \
	python -m pytest -v -ra -k test_checkov tests

test:
	export PYTHONPATH=./backend:/./tests && \
	python -m pytest -v -ra tests/

integration-tests: upgrade-pip install-integration-tests
	export PYTHONPATH=./backend:/./tests_new && \
	python -m pytest -v -ra tests_new/integration_tests/ \
		--junitxml=reports/integration_tests.xml

coverage: upgrade-pip install-backend install-cdkproxy install-tests
	export PYTHONPATH=./backend:/./tests && \
	python -m  pytest -x -v -ra tests/ \
		--junitxml=reports/test-unit.xml \
		--cov-report xml:cobertura.xml \
		--cov-report term-missing \
		--cov-report html \
		--cov=backend/dataall \
		--cov-config=.coveragerc \
		--color=yes

deploy-image:
	docker build -f backend/docker/prod/${type}/Dockerfile -t ${image-tag}:${image-tag} . && \
	aws ecr get-login-password --region ${region} | docker login --username AWS --password-stdin ${account}.dkr.ecr.${region}.amazonaws.com && \
	docker tag ${image-tag}:${image-tag} ${account}.dkr.ecr.${region}.amazonaws.com/${repo}:${image-tag} && \
	docker push ${account}.dkr.ecr.${region}.amazonaws.com/${repo}:${image-tag}

assume-role:
	aws sts assume-role --role-arn "arn:aws:iam::${REMOTE_ACCOUNT_ID}:role/${REMOTE_ROLE}" --external-id ${EXTERNAL_ID} --role-session-name "session1" >.assume_role_json
	echo "export AWS_ACCESS_KEY_ID=$$(cat .assume_role_json | jq '.Credentials.AccessKeyId' -r)" >.env.assumed_role
	echo "export AWS_SECRET_ACCESS_KEY=$$(cat .assume_role_json | jq '.Credentials.SecretAccessKey' -r)" >>.env.assumed_role
	echo "export AWS_SESSION_TOKEN=$$(cat .assume_role_json | jq '.Credentials.SessionToken' -r)" >>.env.assumed_role
	rm .assume_role_json

drop-tables: upgrade-pip install-backend
	pip install 'alembic'
	export PYTHONPATH=./backend && \
	python backend/migrations/drop_tables.py

upgrade-db: upgrade-pip install-backend
	pip install 'alembic'
	export PYTHONPATH=./backend && \
	alembic -c backend/alembic.ini upgrade head

generate-migrations: upgrade-pip install-backend
	pip install 'alembic'
	export PYTHONPATH=./backend && \
	alembic -c backend/alembic.ini upgrade head
	alembic -c backend/alembic.ini revision -m "describe_changes_shortly" --autogenerate

clean:
	@rm -fr cdk_out/
	@rm -fr dist/
	@rm -fr htmlcov/
	@rm -fr site/
	@rm -fr .eggs/
	@rm -fr cdk_out/
	@rm -fr .tox/
	@find . -name '*.egg-info' -exec rm -fr {} +
	@find . -name "*.py[co]" -o -name .pytest_cache -exec rm -rf {} +
	@find . -name '*.egg' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +
