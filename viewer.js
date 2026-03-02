AFRAME.registerComponent("socket-scrub", {
	init: function () {
		this.camera = this.el;
		this.connected = false;
		this.isBusy = false;

		this.delayFrames = 0;
		this.isLeftMsg = true;
		this.hudText = document.getElementById("hud-text");

		this.leftMesh = document
			.getElementById("left-plane")
			.getObject3D("mesh");
		this.rightMesh = document
			.getElementById("right-plane")
			.getObject3D("mesh");

		window.addEventListener("keydown", (e) => {
			if (e.key === "ArrowUp") {
				this.delayFrames++;
			} else if (e.key === "ArrowDown") {
				this.delayFrames--;
			}
		});

		const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
		const wsUrl = `${protocol}//${window.location.host}/ws`;

		console.log("Connecting to", wsUrl);
		this.ws = new WebSocket(wsUrl);
		this.binaryType = "arraybuffer";

		this.ws.onopen = () => {
			console.log("WebSocket Connected");
			this.connected = true;
		};

		this.ws.onmessage = async (event) => {
			const buffer = event.data;
			const dataView = new DataView(buffer);
			const leftLength = dataView.getUint32(0, false);

			const leftView = new Uint8Array(buffer, 4 + leftLength);
			const rightView = new Uint8Array(buffer, 4 + leftLength);

			const leftBlob = new Blob([leftView], { type: "image/jpeg" });
			const rightBlob = new Blob([rightView], { type: "image/jpeg" });

			const [imgL, imgR] = await Promise.all([
				createImageBitmap(leftBlob),
				createImageBitmap(rightBlob),
			]);

			if (this.leftMesh && this.leftMesh.material.map) {
				this.leftMesh.material.map.image = imgL;
				this.leftMesh.material.map.needsUpdate = true;
			}
			if (this.rightMesh && this.rightMesh.material.map) {
				this.rightMesh.material.map.image = imgR;
				this.rightMesh.material.map.needsUpdate = true;
			}

			this.isBusy = false;
		};

		this.ws.onclose = () => {
			this.connected = false;
		};
	},

	tick: function () {
		if (!this.connected || this.isBusy) return;

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
				`Yaw: ${degrees} | ${percent}% | Delay: ${this.delayFrames}`,
			);
		}

		const payload = JSON.stringify({
			pct: pct,
			delay: this.delayFrames,
		});

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
		this.el.addEventListener("axismove", (evt) => {
			const scrubber =
				document.querySelector("[socket-scrub]").components[
					"socket-scrub"
				];
			if (!scrubber) return;

			const yAxis = evt.detail.axis[1];

			if (yAxis > 0.5) {
				setTimeout(() => {
					scrubber.delayFrames++;
				}, 200);
			} else if (yAxis < -0.5) {
				setTimeout(() => {
					scrubber.delayFrames--;
				}, 200);
			}
		});

		this.el.addEventListener("triggerdown", () => {
			const scrubber =
				document.querySelector("[socket-scrub]").components[
					"socket-scrub"
				];
			if (scrubber) scrubber.delayFrames = 0;
		});
	},
});
