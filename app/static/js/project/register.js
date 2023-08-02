import {badge_raw2hex} from "../base/decode_rfid.js";

let badge_input = document.querySelector("#badge-input");
let badge_box_element = document.querySelector("#badge-box");
let badge_box_current_background = badge_box_element.style.background;

export const badge_process_badge = async event => {
    if (event.key === 'Enter') {
        let msg = '';
        let popup_delay = 2000;
        const res = badge_raw2hex(badge_input.value);
        badge_input.value = '';

        if (res.valid) {
            const ret = await fetch(Flask.url_for('register.registration_new', {location_key: location_key, badge_code: res.code}) );
            const status = await ret.json();
            if (status.status) {
                badge_box_element.style.background = status.data.direction === "in" ? "green" : "blue";
                msg = `Dag ${status.data.voornaam}, je ${ status.data.direction === "in" ? "komt binnen"  : "gaat buiten" } om ${status.data.time}`;
                popup_delay = ("popup_delay" in status.data) ? status.data.popup_delay : popup_delay;
            } else {
                badge_box_element.style.background = "red";
                msg = status.data;
            }
        } else {
            badge_box_element.style.background = "red";
            msg = `${res.code} is geen geldige code`;
        }
        setTimeout(() => {badge_box_element.style.background = badge_box_current_background}, popup_delay);
    }
}

const set_focus_on_badge_input = () => {
    badge_input.focus();
    setTimeout(set_focus_on_badge_input, 1000);
}

$(document).ready(function () {
    set_focus_on_badge_input();
});


