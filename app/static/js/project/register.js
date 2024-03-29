import {badge_raw2hex} from "../base/decode_rfid.js";

let badge_input = document.querySelector("#badge-input");
let badge_box_element = document.querySelector("#badge-box");
let badge_box_current_background = badge_box_element.style.background;

export const badge_process_badge = async event => {
    if (event.key === 'Enter') {
        let msg = '';
        let popup_delay = 2000;
        let notification_color = "red";
        const res = badge_raw2hex(badge_input.value);
        badge_input.value = '';
        if (res.valid) {
            const fret = await fetch(Flask.url_for('api.registration_add'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({location_key, badge_code: res.code})});
            const jret = await fret.json();
            if (jret.status) {
                notification_color = "green";
                popup_delay = 200;
            }
        }
        badge_box_element.style.background = notification_color;
        setTimeout(() => badge_box_element.style.background = badge_box_current_background, popup_delay);
    }
}

const set_focus_on_badge_input = () => {
    badge_input.focus();
    setTimeout(set_focus_on_badge_input, 1000);
}

$(document).ready(function () {
    set_focus_on_badge_input();
});


