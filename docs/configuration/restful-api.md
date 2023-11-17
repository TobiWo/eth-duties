# RESTful API

Eth-duties offers the possibility to start a rest server with some basic endpoints. This is a very simple implemenation which starts a rest server on your localhost. The server can be started with flag `--rest`. The port can be modified with `--rest-port`. Additionally you can change the host from which connections are accepted with `--rest-host`. The full swagger spec can be accessed (using default port 5000) via [http://localhost:5000/docs](http://localhost:5000/docs).

This functionality can be used to e.g. create own automation scripts for updating your Ethereum clients.

Beside that it is now also possible to add and remove validator identifiers via rest calls. Some notes for these endpoints:

1. You will receive a **201 (ADD)** or **200 (DELETE)** with the corresponding added/deleted validator identifiers
    * If the number of returned identifiers does not match the number of provided identifiers, the missing ones are in a bad format
    * If identifiers already exist (while calling the **ADD** endpoint) or are not present (while calling the **DELETE** endpoint) no error will be returned
    * For adding new identifiers the rest endpoint accepts the same formats as the [--validators](./validator-identifiers.md/#accepted-formats) flag during startup
1. You will receive a 400 while only providing bad formatted identifiers
1. Check also the logs which are more verbose if you sent a bad formatted identifier
