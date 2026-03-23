AFRAME.registerComponent('uv-shift', {
    schema: {
        shiftX: { type: 'number', default: 0.0 }
    },
    init: function () {
        const applyMaterial = () => {
            const mesh = this.el.getObject3D('mesh');
            if (!mesh || this.materialApplied) return;

            const map = mesh.material.map || null;
            this.shaderMat = new THREE.ShaderMaterial({
                uniforms: {
                    src: { value: map },
                    shiftX: { value: this.data.shiftX }
                },
                vertexShader: `
                    varying vec2 vUv;
                    void main() {
                        vUv = uv;
                        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                    }
                `,
                fragmentShader: `
                    varying vec2 vUv;
                    uniform sampler2D src;
                    uniform float shiftX;
                    void main() {
                        vec2 shiftedUv = vec2(vUv.x + shiftX, vUv.y);
                        if (shiftedUv.x < 0.0 || shiftedUv.x > 1.0) {
                            gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
                        } else {
                            gl_FragColor = texture2D(src, shiftedUv);
                        }
                    }
                `
            });
            mesh.material = this.shaderMat;
            this.materialApplied = true;
        };

        this.el.addEventListener('object3dset', applyMaterial);
        if (this.el.getObject3D('mesh')) applyMaterial();
    },
    update: function () {
        if (this.shaderMat) {
            this.shaderMat.uniforms.shiftX.value = this.data.shiftX;
        }
    }
});

AFRAME.registerComponent("socket-scrub", {
    init: function () {
        this.camera = this.el;
        this.connected = false;
        this.isBusy = false;

        this.delayFrames = 0;
        this.convergence = 0; 
        this.hudText = document.getElementById("hud-text");

        window.addEventListener("keydown", (e) => {
            if (e.key === "ArrowUp") this.delayFrames++;
            if (e.key === "ArrowDown") this.delayFrames--;
            if (e.key === "ArrowLeft") this.sendAction("prev");
            if (e.key === "ArrowRight") this.sendAction("next");
            if (e.key === "a" || e.key === "A") this.convergence -= 0.002;
            if (e.key === "d" || e.key === "D") this.convergence += 0.002;
        });

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);
        this.ws.binaryType = "arraybuffer";
        this.ws.onopen = () => { this.connected = true; };

        this.ws.onmessage = async (event) => {
            try {
                const buffer = event.data;
                const dataView = new DataView(buffer);
                const leftLength = dataView.getUint32(0, false);

                const leftView = new Uint8Array(buffer, 4, leftLength);
                const rightView = new Uint8Array(buffer, 4 + leftLength);

                const leftBlob = new Blob([leftView], { type: "image/jpeg" });
                const rightBlob = new Blob([rightView], { type: "image/jpeg" });

                const [imgL, imgR] = await Promise.all([
                    createImageBitmap(leftBlob),
                    createImageBitmap(rightBlob),
                ]);

                const leftPlane = document.getElementById("left-plane");
                const rightPlane = document.getElementById("right-plane");

                const updateTexture = (plane, img) => {
                    if (!plane) return;
                    const mesh = plane.getObject3D("mesh");
                    if (!mesh || !mesh.material) return;
                    
                    if (mesh.material.uniforms && mesh.material.uniforms.src) {
                        let tex = mesh.material.uniforms.src.value;
                        if (!tex || !tex.isTexture) {
                            tex = new THREE.Texture(img);
                            tex.minFilter = THREE.LinearFilter;
                            tex.magFilter = THREE.LinearFilter;
                            mesh.material.uniforms.src.value = tex;
                        } else {
                            tex.image = img;
                        }
                        tex.needsUpdate = true;
                    } else if (mesh.material.map) {
                        mesh.material.map.image = img;
                        mesh.material.map.needsUpdate = true;
                    }
                };

                updateTexture(leftPlane, imgL);
                updateTexture(rightPlane, imgR);

            } catch (err) {
                console.error("Frame decode error:", err);
            } finally {
                this.isBusy = false; 
            }
        };

        this.ws.onclose = () => { this.connected = false; };
    },

    sendAction: function(actionType) {
        if (!this.connected || !this.ws) return;
        this.ws.send(JSON.stringify({ action: actionType }));
        this.isBusy = false; 
    },

    tick: function (time, timeDelta) {
        if (time - this.lastTickTime < this.tickInterval) return;
        this.lastTickTime = time;


        if (!this.connected || this.isBusy) return;

        const rotY = -this.camera.object3D.rotation.y;
        const PI2 = Math.PI * 2;
        let normalizedRot = rotY % PI2;
        if (normalizedRot < 0) normalizedRot += PI2;
        const pct = normalizedRot / PI2;

        if (this.hudText) {
            const degrees = (normalizedRot * (180 / Math.PI)).toFixed(1);
            const percent = Math.round(pct * 100);
            const convDisplay = this.convergence.toFixed(3);
            this.hudText.setAttribute(
                "value",
                `Yaw: ${degrees} | ${percent}% | Delay: ${this.delayFrames} | Conv: ${convDisplay}`
            );
        }

        const leftPlane = document.getElementById("left-plane");
        const rightPlane = document.getElementById("right-plane");
        if (leftPlane && rightPlane) {
            leftPlane.setAttribute("uv-shift", "shiftX", -this.convergence);
            rightPlane.setAttribute("uv-shift", "shiftX", this.convergence);
        }

        this.ws.send(JSON.stringify({ pct: pct, delay: this.delayFrames }));
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
        this.lastMoveTimeY = 0;
        this.lastMoveTimeX = 0;
        this.lastTickTime = 0;
        this.targetFps = 40;
        this.tickInterval = 1000 / this.targetFps;

        this.el.addEventListener("axismove", (evt) => {
            const scrubberEl = document.querySelector("[socket-scrub]");
            if (!scrubberEl || !scrubberEl.components["socket-scrub"]) return;
            const scrubber = scrubberEl.components["socket-scrub"];
            const now = Date.now();
            const axes = evt.detail.axis;
            
            let xAxis = axes.length >= 4 ? axes[2] : axes[0];
            let yAxis = axes.length >= 4 ? axes[3] : axes[1];

            if (Math.abs(yAxis) > 0.5 && now - this.lastMoveTimeY > 150) {
                if (yAxis > 0.5) scrubber.delayFrames++;
                else scrubber.delayFrames--;
                this.lastMoveTimeY = now;
            }
            if (Math.abs(xAxis) > 0.6 && now - this.lastMoveTimeX > 500) {
                if (xAxis > 0.6) scrubber.sendAction("next");
                else scrubber.sendAction("prev");
                this.lastMoveTimeX = now;
            }
        });

        this.el.addEventListener("triggerdown", () => {
            const scrubberEl = document.querySelector("[socket-scrub]");
            if (scrubberEl && scrubberEl.components["socket-scrub"]) {
                scrubberEl.components["socket-scrub"].delayFrames = 0;
                scrubberEl.components["socket-scrub"].convergence = 0;
            }
        });
    },
});