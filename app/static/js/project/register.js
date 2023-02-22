import {badge_raw2hex} from "../base/decode_rfid.js";

let badge_input = document.querySelector(("#badge-input"))

export const badge_process_badge = async event => {
    if (event.key === 'Enter') {
        let msg = '';
        const res = badge_raw2hex(badge_input.value);
        badge_input.value = '';

        if (res.valid) {
            const ret = await fetch(Flask.url_for('register.registration_new', {location_key: location_key, badge_code: res.code}), {headers: {'x-api-key': api_key,}});
            const status = await ret.json();
            if (status.status) {
                msg = `Dag ${status.data.voornaam}, je ${ status.data.direction === "in" ? "komt binnen"  : "gaat buiten" } om ${status.data.time}`;
            } else {
                msg = status.data;
            }
        } else {
            msg = `${res.code} is geen geldige code`;
        }
        let bb_alert = bootbox.alert(msg);
        setTimeout(() => {bb_alert.modal("hide")}, 2000);
    }
}

const set_focus_on_badge_input = () => {
    badge_input.focus();
    setTimeout(set_focus_on_badge_input, 1000);
}

$(document).ready(function () {
    set_focus_on_badge_input();
});


