FROM node:21.2.0

WORKDIR /app
COPY semver.js /app/semver.js

RUN npm update -g npm
RUN npm install semver

CMD ["npm", "start"]

# docker build -f npm.dockerfile . -t dependabot/npm:latest
# docker run dependabot/npm:latest bash -c "node semver.js FUNC ARG1 [ARG2] ..."
# docker compose run node bash -c "node semver.js gt '1.3.3' '2.2.1'"