# thread-viewer

## Layer loading behavior
Layer 0 and layer 1 are loaded implicitly and in a blocking mode at server startup.

Next layers are loaded when `{"action": "next"}` is specified in a websocket request from the connection.

Since loading a layer (except for 0, 1) starts an asynchronous process if user requests a new layer while one is being loaded the process will start just fine.

Of course loading multiple layers at once will slow the process down significantly