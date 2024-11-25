import {Rfid} from "./rfidusb.js";

$(document).ready(function () {
    Rfid.init();
    Rfid.set_location("timeregistration")
    Rfid.set_managed_state(true);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            Rfid.set_location("timeregistration")
        }
    });
});


