import { create_context_menu, subscribe_right_click } from "../base/right_click.js";
import { ctx, get_data_of_row } from "../datatables/datatables.js"
import {socketio} from "../base/socketio.js";
import { formio_popup_create } from "../base/popup.js"

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


const export_student_balance_items = ["sui-drank", "sul-drank"]

const export_student_balances_cb = (action, opaque, data=null) => {
    if (action === 'submit') {
        export_student_balance_items.forEach(item => window.open(`/student/export/${item}/${data.startdate}/${data.enddate}`, '_blank'))
    }
}

const papercut_items = ["sui", "sul", "sum"]

const upload_papercut = async () =>  {
    const form = document.createElement("form")
    const input = document.createElement('input');
    form.appendChild(input)
    input.type = 'file';
    input.name = "papercut_file";
    input.multiple = true;
    input.accept = ".xlsx,.xls, .csv"
    input.onchange = async e => {
        var file = e.target.files[0];
        const form_data = new FormData(form);
        const ret = await fetch(Flask.url_for('api.papercut_upload'), {headers: {'x-api-key': api_key,}, method: 'POST', body: form_data});
        const status = await ret.json();
        if (status.status) {
            papercut_items.forEach(item => window.open(`/student/papercut/export/${item}`, '_blank'))
        } else {
             bootbox.alert(status.data)
        }
    }
    input.click();
}


const export_student_balances = (popup) => {
    console.log("yes")
    formio_popup_create(popup, export_student_balances_cb);
}



let context_menu = [{type: "divider"}, {type: "item", iconscout: "wifi", label: "RFID code aanpassen", cb: __reserve_student_rfid},]
$(document).ready(function () {
const current_location = localStorage.getItem("view-location");
    context_menu.unshift({type: "item", iconscout: "plus-circle", label: `Nieuwe registratie: ${locations[current_location].locatie}`, cb: ids => __registration_add(current_location, ids)});
    create_context_menu(context_menu);
    socketio.start(null, null);
    socketio.subscribe_on_receive("update-status", __socketio_update_status);
    subscribe_right_click('export-student-balance', (item, ids) => export_student_balances(ctx.popups['export-student-balance']));
    subscribe_right_click('export-papercut-balance', (item, ids) => upload_papercut());
});

const __socketio_update_status = (type, data) => {
    alert(`${data.data}`);
}