#!/bin/bash
here_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
proj_dir="$here_dir/.."

set -x
work=postcard-love

docker run -p 3000:3000 -p 3001:3001  --name $work -v "$proj_dir:/$work" \
    -w /$work  -it -d $work /bin/bash || true

docker start $work || true

CMD=${1:-}
if [ -z "$CMD" ]; then
    docker attach $work
else
    docker exec -it $work bash -i -c "$CMD"
fi
