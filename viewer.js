AFRAME.registerComponent("socket-scrub", {
    init: function () {
        this.camera = this.el;
        this.currentLayer = 0;
        this.delayFrames = 0;
        this.frameCounter = 0;
        
        this.hudText = document.getElementById("hud-text");
        this.leftMesh = document.getElementById("left-plane").getObject3D("mesh");
        this.rightMesh = document.getElementById("right-plane").getObject3D("mesh");

        this.connectToLayer(this.currentLayer);
    },

    connectToLayer: function (layerIdx) {
        if (this.ws) {
            this.ws.close();
        }

        this.connected = false;
        this.isBusy = false;
        this.currentLeftFrame = null;
        this.currentRightFrame = null;

        // Recreate decoders to flush old state and memory
        if (this.leftDecoder) this.leftDecoder.close();
        if (this.rightDecoder) this.rightDecoder.close();

        this.leftDecoder = new VideoDecoder({
            output: (frame) => {
                if (this.currentLeftFrame) this.currentLeftFrame.close();
                this.currentLeftFrame = frame;
                if (this.leftMesh && this.leftMesh.material.map) {
                    this.leftMesh.material.map.image = frame;
                    this.leftMesh.material.map.needsUpdate = true;
                }
            },
            error: (e) => console.error("Left Decoder Error:", e)
        });

        this.rightDecoder = new VideoDecoder({
            output: (frame) => {
                if (this.currentRightFrame) this.currentRightFrame.close();
                this.currentRightFrame = frame;
                if (this.rightMesh && this.rightMesh.material.map) {
                    this.rightMesh.material.map.image = frame;
                    this.rightMesh.material.map.needsUpdate = true;
                }
                this.isBusy = false; 
            },
            error: (e) => console.error("Right Decoder Error:", e)
        });

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/${layerIdx}`;

        this.ws = new WebSocket(wsUrl);
        this.ws.binaryType = "arraybuffer";

        this.ws.onopen = () => {
            this.connected = true;
        };

        this.ws.onmessage = (event) => {
            const buffer = event.data;
            const dataView = new DataView(buffer);
            const type = dataView.getUint8(0);

            if (type === 0) {
                const extradata = new Uint8Array(buffer, 1);
                const config = {
                    codec: 'avc1.4D002A',
                    description: extradata,
                    optimizeForLatency: true
                };
                this.leftDecoder.configure(config);
                this.rightDecoder.configure(config);
            } else if (type === 1) {
                const leftLength = dataView.getUint32(1, false);
                const leftView = new Uint8Array(buffer, 5, leftLength);
                const rightView = new Uint8Array(buffer, 5 + leftLength);

                const leftChunk = new EncodedVideoChunk({ type: 'key', timestamp: this.frameCounter * 1000, data: leftView });
                const rightChunk = new EncodedVideoChunk({ type: 'key', timestamp: this.frameCounter * 1000, data: rightView });

                this.frameCounter++;

                try {
                    this.leftDecoder.decode(leftChunk);
                    this.rightDecoder.decode(rightChunk);
                } catch (e) {
                    this.isBusy = false;
                }
            }
        };
    },

    changeLayer: function (direction) {
        this.currentLayer += direction;
        if (this.currentLayer < 0) this.currentLayer = 0;
        this.connectToLayer(this.currentLayer);
    },

    tick: function () {
        if (!this.connected || this.isBusy || this.leftDecoder.state !== "configured") return;

        const rotY = -this.camera.object3D.rotation.y;
        const PI2 = Math.PI * 2;
        let normalizedRot = rotY % PI2;

        if (normalizedRot < 0) normalizedRot += PI2;
        const pct = normalizedRot / PI2;

        if (this.hudText) {
            const degrees = (normalizedRot * (180 / Math.PI)).toFixed(1);
            const percent = Math.round(pct * 100);
            this.hudText.setAttribute(
                "value",
                `Layer: ${this.currentLayer} | Yaw: ${degrees} | ${percent}% | Delay: ${this.delayFrames}`
            );
        }

        const payload = JSON.stringify({ pct: pct, delay: this.delayFrames });
        this.ws.send(payload);
        this.isBusy = true;
    },
});

AFRAME.registerComponent("stereo-layer", {
    schema: { eye: { type: "string", default: "left" } },
    init: function () {
        const layerMask = this.data.eye === "left" ? 1 : 2;
        this.el.object3D.traverse((node) => {
            if (node.isMesh) node.layers.set(layerMask);
        });
    },
});

AFRAME.registerComponent("controller", {
    init: function () {
        this.lastMoveTime = 0;
        this.lastXMoveTime = 0;

        // Keyboard bindings for testing
        window.addEventListener("keydown", (e) => {
            const scrubber = document.querySelector("[socket-scrub]").components["socket-scrub"];
            if (!scrubber) return;

            if (e.key === "ArrowUp") scrubber.delayFrames++;
            if (e.key === "ArrowDown") scrubber.delayFrames--;
            if (e.key === "ArrowLeft") scrubber.changeLayer(-1);
            if (e.key === "ArrowRight") scrubber.changeLayer(1);
        });

        // VR Controller trackpad bindings
        this.el.addEventListener("axismove", (evt) => {
            const scrubber = document.querySelector("[socket-scrub]").components["socket-scrub"];
            if (!scrubber) return;

            const now = Date.now();
            const xAxis = evt.detail.axis[0];
            const yAxis = evt.detail.axis[1];

            // Y-Axis for Delay
            if (now - this.lastMoveTime > 200) {
                if (yAxis > 0.5) {
                    scrubber.delayFrames++;
                    this.lastMoveTime = now;
                } else if (yAxis < -0.5) {
                    scrubber.delayFrames--;
                    this.lastMoveTime = now;
                }
            }

            // X-Axis for Layer Switch
            if (now - this.lastXMoveTime > 500) {
                if (xAxis > 0.6) {
                    scrubber.changeLayer(1);
                    this.lastXMoveTime = now;
                } else if (xAxis < -0.6) {
                    scrubber.changeLayer(-1);
                    this.lastXMoveTime = now;
                }
            }
        });

        this.el.addEventListener("triggerdown", () => {
            const scrubber = document.querySelector("[socket-scrub]").components["socket-scrub"];
            if (scrubber) scrubber.delayFrames = 0;
        });
    },
});