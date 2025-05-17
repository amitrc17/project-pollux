# project-pollux

Start Up:
- Load Up your viritual env if you must.
- `cd` into root directory of the project (`/project-pollux`) and run `redis-server`. This should start the redis DB server on port 6379. Note that it will create (and load) a redis.rdb file in this directory to store your db interactions.
- In a different terminal window, `cd` into `project-pollux/webapp/web directory` and run `yarn start-api`. This should run the flask backend server on port 5000.
- In a different terminal window, `cd` into `project-pollux/webapp/web directory` and run `npm start`. This should start the react app for the web UI on port 3000.
- Finally, you can start interacting with the web UI.
