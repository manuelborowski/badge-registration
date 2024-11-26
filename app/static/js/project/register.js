import {Rfid} from "./rfidusb.js";
import {socketio} from "../base/socketio.js";

$(document).ready(function () {
    socketio.start(null, null);
    socketio.subscribe_to_room("timeregistration");
    socketio.subscribe_on_receive("update-list-of-registrations", __socketio_update_list);
    socketio.subscribe_on_receive("update-items-in-list-of-registrations", __socketio_update_item_in_list);
    Rfid.init();
    Rfid.set_location("timeregistration")
    Rfid.set_managed_state(true);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            Rfid.set_location("timeregistration")
        }
    });
    __update_clock();
});

let timer_id = null;

// Called when the staff member badges in
const __socketio_update_list = (type, data) => {
    if (data.status && data.action === "add") {
        if (timer_id !== null) clearTimeout(timer_id);
        document.querySelector("#line1").innerHTML = `${data.data[0].voornaam} ${data.data[0].naam}<br>Je bent IN gescand om: ${data.data[0].timestamp}`
        document.querySelector("#popup-box").style.display = "flex";
        timer_id = setTimeout(() => document.querySelector("#popup-box").style.display = "none", 8000);

    }
}

// Called when the staff member badges out (and this in-out option is configured)
const __socketio_update_item_in_list = (type, data) => {
    if (data.status) {
        if (timer_id !== null) clearTimeout(timer_id);
        document.querySelector("#line1").innerHTML = `${data.data[0].voornaam} ${data.data[0].naam}<br>Je bent IN gescand om: ${data.data[0].time_in}<br>Je bent UIT gescand om: ${data.data[0].time_out}`
        document.querySelector("#popup-box").style.display = "flex";
        timer_id = setTimeout(() => document.querySelector("#popup-box").style.display = "none", 8000);
    }
}


const __update_clock = () => {
    const now = new Date();
    const options = {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',};
    const timestring = `${now.toLocaleDateString('nl-BE', options)} ${now.toLocaleTimeString('nl-BE')}`;
    document.querySelector("#clock").innerHTML = timestring;
    setTimeout(__update_clock, 1000);
}


