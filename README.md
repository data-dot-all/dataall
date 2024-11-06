# GH Pages Branch

### Local Development

To launch the docs locally at http://localhost:4000 use the following command

`docker run --name ghpages --rm -e JEKYLL_UID=$(id -u) -e JEKYLL_GID=$(id -g) -v jekyllb:/usr/local/bundle -v .:/srv/jekyll:Z -p 4000:4000 -it jekyll/jekyll:3 jekyll serve`