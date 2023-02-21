import {badge_raw2hex} from "../base/decode_rfid.js";

export const badge_process_badge = async event => {
    if (event.key === 'Enter') {
        let badge_input = document.querySelector(("#badge-input"))
        const res = badge_raw2hex(badge_input.value);
        badge_input.value = '';
        if (res.valid) {
            const ret = await fetch(Flask.url_for('register.registration_new', {location_key: location_key, badge_code: res.code}), {headers: {'x-api-key': api_key,}});
            const status = await ret.json();
            if (status.status) {
                let msg = `Dag ${status.data.voornaam}, je ${ status.data.direction === "in" ? "komt binnen"  : "gaat buiten" } om ${status.data.time}`
                bootbox.alert(msg)
            } else {
                bootbox.alert(status.data)
            }
        } else {
            bootbox.alert(`${res.code} is geen geldige code`);
        }
        badge_input.focus();
    }
}
