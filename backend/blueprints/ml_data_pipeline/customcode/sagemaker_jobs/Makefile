
# ensure virtual targets cannot be confused with sub-directories
.PHONY: clean-venv clean install test release semver
# retreive package name
PACKAGE_NAME := $(shell python setup.py --name)

# retrieve last tag name from git
#This show the error fatal: No names found, cannot describe anything. when repo have no tags.
LAST_TAG := $(shell git describe --abbrev=0 --tags)

# retrieve version from package
CURRENT_VERSION := $(shell python setup.py --version)

GIT_EMAIL := ci@email.com
GIT_NAME := GitName

# Compute semantical versioning for this package
# parameters: <last tag> <setup.py version>
# examples:
#   $(SEMVER) 0.0.1 0.0.1 --> 0.0.2
#	$(SEMVER) 0.0.2 0.0.1 --> 0.0.3
#   $(SEMVER) 0.0.1 0.0.3 --> 0.0.3
define SEMVER_PYSCRIPT
import sys, semver

last_tag, current_version = sys.argv[1:]
result = current_version

if semver.compare(last_tag, current_version) >= 0:
	result = semver.bump_patch(last_tag)

if result != current_version:
	with open("VERSION", "w") as f:
		f.write(result)
	print("Version updated to '%s'" % result)
endef
export SEMVER_PYSCRIPT
SEMVER := python -c "$$SEMVER_PYSCRIPT"


# Basic commands

# help: venv                           - create a virtual environment for development
.PHONY: venv
venv:
	@test -d venv || mkdir -p venv
	@rm -Rf venv
	@python3 -m venv venv
	@/bin/bash -c "source venv/bin/activate"
	@/bin/bash -c "python -m pip install pip --upgrade && python -m pip install -e '.[dev]'"

install: clean
	python -m pip install --upgrade pip setuptools pip
	python -m pip install -e ".[dev]"

flake8:
	python -m flake8 --exit-zero ${PACKAGE_NAME}/ | tee flake8.log || true
	python -m flake8 --ignore=$(FLAKE8_IGNORE) --exit-zero tests/ | tee flake8.log || true

pylint:
	find ./${PACKAGE_NAME} ./tests -name \*.py | xargs python -m pylint $(find handlers -maxdepth 1 -name "*.py" -print)  --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --exit-zero

test:
	python -m pytest -s -x \
		--junitxml=reports/test-unit.xml \
		--cov-report xml:cobertura.xml \
		--cov-report term-missing \
		--cov-report html \
		--cov=${PACKAGE_NAME}

fetch-tags:
	git tag -l | xargs git tag -d >/dev/null && git fetch -t >/dev/null 2>&1

update-version:
	$(SEMVER) $(LAST_TAG) $(CURRENT_VERSION)

release:
	git config --global user.email $(GIT_EMAIL)
	git config --global user.name $(GIT_NAME)
ifeq ($(shell git status | grep VERSION | wc -l), 1)
	git commit -a -m "Update version to $(shell python setup.py --version)"
	git tag $(CURRENT_VERSION)
	git push --set-upstream origin master
else
	git tag ${CURRENT_VERSION}
endif
	git push --tags
