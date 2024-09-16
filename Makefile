PWD=$$(pwd)
SCRIPT_DIR=$(shell cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJ_ROOT=$(SCRIPT_DIR)
RUN_DOCKER=$(PROJ_ROOT)/tools/docker-run.sh

init: 	
	rm -rf node_modules
	$(RUN_DOCKER) "npm install"


build: 	
	$(RUN_DOCKER) "npm run build"
	$(RUN_DOCKER) "tree ./backend/static"


serve:
	$(RUN_DOCKER) "npm run dev"

shell:
	$(RUN_DOCKER) "bash -i"

.PHONY: build
