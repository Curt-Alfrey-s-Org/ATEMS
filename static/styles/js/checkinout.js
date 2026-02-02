document.addEventListener("DOMContentLoaded", function() {
    var form = document.getElementById("myForm");
    var msgDiv = document.getElementById("js-messages");
    var toolInput = document.getElementById("tool_id_number");
    var badgeInput = document.getElementById("badge_id");
    var usernameInput = document.getElementById("username");
    var scanInput = document.getElementById("scanInput");
    var scanCameraBtn = document.getElementById("scanCameraBtn");
    var scanModal = document.getElementById("scanModal");
    var scanModalClose = document.getElementById("scanModalClose");
    var qrReader = document.getElementById("qrReader");

    function showMessage(text, type) {
        var cls = type === "success" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : type === "warning" ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30";
        msgDiv.innerHTML = "<div class=\"px-4 py-3 rounded-lg " + cls + "\">" + text + "</div>";
        msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // Apply scanned value: first scan → tool ID, second → badge (and lookup username)
    function applyScanValue(val) {
        val = (val || "").trim();
        if (!val) return;
        if (!toolInput.value.trim()) {
            toolInput.value = val;
            if (scanInput) scanInput.value = "";
            if (scanInput) scanInput.placeholder = "Now scan badge";
            if (scanInput) scanInput.focus();
            return;
        }
        if (!badgeInput.value.trim()) {
            badgeInput.value = val;
            if (scanInput) scanInput.value = "";
            if (scanInput) scanInput.placeholder = "Scan tool ID, then badge";
            if (scanInput) scanInput.focus();
            // Look up username by badge
            fetch("/api/user-by-badge?badge_id=" + encodeURIComponent(val))
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.username && usernameInput) usernameInput.value = data.username;
                })
                .catch(function() {});
            // Auto-submit when tool + badge are set
            if (usernameInput && usernameInput.value.trim()) {
                setTimeout(function() { form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true })); }, 100);
            }
            return;
        }
        // Both already set: treat as new tool (reset tool, set tool)
        toolInput.value = val;
        badgeInput.value = "";
        if (usernameInput) usernameInput.value = "";
        if (scanInput) scanInput.value = "";
        if (scanInput) scanInput.placeholder = "Now scan badge";
        if (scanInput) scanInput.focus();
    }

    // Scan input: keyboard wedge (scanner sends value + Enter)
    if (scanInput) {
        scanInput.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                applyScanValue(scanInput.value);
            }
        });
    }

    // Camera scan (html5-qrcode)
    var html5QrCode = null;
    function startCameraScan() {
        if (typeof Html5Qrcode === "undefined") {
            showMessage("Camera scanner library not loaded.", "error");
            return;
        }
        if (html5QrCode) return;
        scanModal.classList.remove("hidden");
        html5QrCode = new Html5Qrcode("qrReader");
        html5QrCode.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: { width: 250, height: 250 } },
            function(decodedText) {
                applyScanValue(decodedText);
                stopCameraScan();
            },
            function() {}
        ).catch(function(err) {
            showMessage("Camera error: " + (err.message || "Could not start camera."), "error");
            stopCameraScan();
        });
    }
    function stopCameraScan() {
        if (html5QrCode) {
            html5QrCode.stop().catch(function() {});
            html5QrCode = null;
        }
        scanModal.classList.add("hidden");
    }
    if (scanCameraBtn) scanCameraBtn.addEventListener("click", startCameraScan);
    if (scanModalClose) scanModalClose.addEventListener("click", stopCameraScan);
    if (scanModal) scanModal.addEventListener("click", function(e) { if (e.target === scanModal) stopCameraScan(); });

    form.addEventListener("submit", function(event) {
        event.preventDefault();

        var username = usernameInput ? usernameInput.value : "";
        var badge_id = badgeInput ? badgeInput.value : "";
        var tool_id_number = (toolInput && toolInput.value) || "";

        if (!username || !badge_id || !tool_id_number) {
            showMessage("All fields must be filled out.", "error");
            return;
        }

        fetch("/checkinout", {
            method: "POST",
            body: new FormData(form)
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === "success") {
                var msg = data.message;
                if (data.calibration_warning) msg += " " + data.calibration_warning;
                showMessage(msg, data.calibration_warning ? "warning" : "success");
                if (toolInput) toolInput.value = "";
                if (badgeInput) badgeInput.value = "";
                if (usernameInput) usernameInput.value = "";
                if (scanInput) { scanInput.value = ""; scanInput.placeholder = "Scan tool ID, then badge"; scanInput.focus(); }
            } else {
                showMessage(data.message || "An error occurred.", "error");
            }
        })
        .catch(function(err) {
            console.error("Error:", err);
            showMessage("Network error. Please try again.", "error");
        });
    });
});
