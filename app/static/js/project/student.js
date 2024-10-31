import {create_context_menu} from "../base/right_click.js";
import { ctx, get_data_of_row } from "../datatables/datatables.js"
import {socketio} from "../base/socketio.js";

let menu_item2label = {};

const __registration_add = async (item, ids) => {
   let person = get_data_of_row(ids[0]);
    bootbox.confirm(`Registratie: ${locations[item].locatie}<br>Voor: ${person.naam} ${person.voornaam}`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_add'),
                {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({location_key: item, leerlingnummer: person.leerlingnummer})});
            const status = await ret.json();
            if (status.status) {
            } else {
                bootbox.alert(status.data)
            }
            ctx.reload_table();
        }
    });
}

const __reserve_student_rfid = async (ids) => {
    const current_location = localStorage.getItem("view-location");
    const person = get_data_of_row(ids[0]);
    bootbox.confirm(`Nieuwe RFID voor: ${person.naam} ${person.voornaam}<br>Druk op ok en u heeft ${reservation_margin} seconden om de badge te registreren`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.reserve_item'),
                {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({location_key: current_location, leerlingnummer: person.leerlingnummer, item: "rfid"})});
            const status = await ret.json();
            if (status.status) {
            } else {
                bootbox.alert(status.data)
            }
            ctx.reload_table();
        }
    });

}


let context_menu = [{type: "divider"}, {type: "item", iconscout: "wifi", label: "RFID code aanpassen", cb: __reserve_student_rfid},]
$(document).ready(function () {
    const current_location = localStorage.getItem("view-location");
    context_menu.unshift({type: "item", iconscout: "plus-circle", label: `Nieuwe registratie: ${locations[current_location].locatie}`, cb: ids => __registration_add(current_location, ids)});
    create_context_menu(context_menu);
    socketio.start(null, null);
    socketio.subscribe_on_receive("update-status", __socketio_update_status);
});

const __socketio_update_status = (type, data) => {
    alert(`${data.data}`);
}