import {Rfid} from "./rfidusb.js";
import {socketio} from "../base/socketio.js";
import {get_my_ip, check_server_alive, timed_popup} from "../base/misc.js";

$(document).ready(async function () {
    socketio.start(null, null);
    socketio.subscribe_to_room(await get_my_ip());
    socketio.subscribe_on_receive("alert-popup", (type, data) => timed_popup(type, data, 3000));
    Rfid.init();
    Rfid.set_location("timeregistration")
    Rfid.set_managed_state(true);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) Rfid.set_location("timeregistration")
    });
    __update_clock();
    __reload_page();
    check_server_alive();
});

const __update_clock = () => {
    const now = new Date();
    const options = {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',};
    document.querySelector("#clock").innerHTML = `${now.toLocaleDateString('nl-BE', options)} ${now.toLocaleTimeString('nl-BE')}`;
    setTimeout(__update_clock, 1000);
}

let __logged_once = false;
// reload the page at certain moments to reset the socketio connections
const __reload_page = () => {
    const today = new Date().toDateString();
    const now = Date.now();
    let moments = reload_page_moments.map(m => Date.parse(`${today} ${m} GMT+1`)).sort();
    moments.push(moments[0] + 24 * 3600 * 1000);  // first moment is added at end with 24 hours added to handle array overflow
    let stored_moment = parseInt(localStorage.getItem("reload_page_at"));
    if (stored_moment === null || !moments.includes(stored_moment)) { // Not stored yet, store the first (earliest) moment
        localStorage.setItem("reload_page_at", moments[0]);
        stored_moment = moments[0];
    }
    if (!__logged_once) {
        console.log(`Next reload at ${new Date(stored_moment)}`);
        __logged_once = true;
    }
    if (now >= stored_moment) {
        const next_moment = moments.filter(m => m > now)[0];
        localStorage.setItem("reload_page_at", next_moment);
        location.reload();
    }
    setTimeout(__reload_page, 1000 * 10);
}
