document.addEventListener("DOMContentLoaded", function() {
    var form = document.getElementById("myForm");
    var msgDiv = document.getElementById("js-messages");
    var toolInput = document.getElementById("tool_id_number");

    function showMessage(text, type) {
        var cls = type === "success" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : type === "warning" ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30";
        msgDiv.innerHTML = "<div class=\"px-4 py-3 rounded-lg " + cls + "\">" + text + "</div>";
        msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    form.addEventListener("submit", function(event) {
        event.preventDefault();

        var username = document.getElementById("username").value;
        var badge_id = document.getElementById("badge_id").value;
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
                if (toolInput) toolInput.value = "";  // Ready for next scan
                toolInput && toolInput.focus();
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